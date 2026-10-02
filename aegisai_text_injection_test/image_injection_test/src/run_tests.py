import argparse
import csv
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.dirname(__file__))
from agent import run_defended, run_undefended
from detector import inspect
from image_sets import load_samples
from model_eval import ensure_ollama_models, evaluate, installed_vision_model_specs, parse_specs, show_image_models, summarize
from prompt_lab import choose_attack_prompt, choose_defense_prompt, combine_attack_prompts, load_pack, overlay_prompt
from interactive import configure as configure_interactive

DEFAULT_CORPUS = os.path.join(ROOT, "corpus", "image_injection_corpus_v1.0.0.json")
MODELS_PATH = os.path.join(ROOT, "models.json")
PROMPTS_PATH = os.path.join(ROOT, "prompts.json")
RESULTS_DIR = os.path.join(ROOT, "results")
CPU_PROFILES = {
    "8gb": {"model": "ollama:moondream", "max_samples": 1, "timeout": 300, "note": "Safest CPU-only option; use one image at a time."},
    "16gb": {"model": "ollama:qwen2.5vl:3b", "max_samples": 2, "timeout": 300, "note": "Higher-capability CPU option; keep the test small."},
    "more": {"model": "ollama:llava", "max_samples": 4, "timeout": 600, "note": "Larger CPU option; expect slow inference and monitor memory."},
}


def _pct(number, total):
    return round(100 * number / total, 1) if total else 0.0


def _archive_results():
    if not os.path.isdir(RESULTS_DIR):
        return None
    existing = [name for name in os.listdir(RESULTS_DIR) if name != "history"]
    if not existing:
        return None
    archive_name = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive_dir = os.path.join(RESULTS_DIR, "history", archive_name)
    os.makedirs(archive_dir, exist_ok=True)
    for name in existing:
        source = os.path.join(RESULTS_DIR, name)
        target = os.path.join(archive_dir, name)
        if os.path.isdir(source):
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    return archive_dir


def print_capability_list():
    with open(MODELS_PATH, encoding="utf-8") as file:
        catalog = json.load(file).get("catalog", [])
    with open(PROMPTS_PATH, encoding="utf-8") as file:
        prompts = json.load(file)
    print("Available models")
    for entry in catalog:
        provider = entry["id"].split(":", 1)[0]
        kind = "vision/image" if entry.get("vision") else ("OCR fallback" if provider == "ollama" else "hosted/API")
        size = entry.get("download_size", "API or size not listed")
        print(f"  {entry['id']:40s} {kind:14s} {size}")
    print("\nAttack methods")
    for entry in prompts.get("attack_prompts", []):
        print(f"  {entry['id']:20s} {entry['name']}")
    print("\nDefense methods")
    for entry in prompts.get("defense_prompts", []):
        print(f"  {entry['id']:20s} {entry['name']}")
    print("\nUse --capability-report after a model comparison to print measured percentages.")


def print_capability_report():
    path = os.path.join(RESULTS_DIR, "model_comparison.json")
    if not os.path.exists(path):
        raise RuntimeError("Missing results/model_comparison.json. Run a model comparison first.")
    with open(path, encoding="utf-8") as file:
        comparison = json.load(file)
    print("Latest attack and defense capability report")
    print("MODEL                                      MODE             INPUT          ATTACK SUCCESS  DEFENSE RATE  FALSE POS  ACCURACY  ERRORS  LATENCY")
    for summary in comparison.get("models", []):
        rows = [row for row in comparison.get("rows", []) if row.get("model") == summary.get("model")]
        mode = rows[0].get("defense_mode", "unknown") if rows else "unknown"
        input_mode = rows[0].get("input_mode", "unknown") if rows else "unknown"
        valid = [row for row in rows if row.get("correct") is not None]
        attacks = [row for row in valid if row.get("label") == "attack"]
        benign = [row for row in valid if row.get("label") == "benign"]
        detection = _pct(sum(row.get("predicted_attack") is True for row in attacks), len(attacks)) if attacks else summary.get("defense_rate_pct", summary.get("attack_detection_rate_pct"))
        attack_success = round(100 - detection, 1) if detection is not None else summary.get("attack_success_rate_pct")
        false_positive = _pct(sum(row.get("predicted_attack") is True for row in benign), len(benign)) if benign else summary.get("false_positive_rate_pct")
        accuracy = _pct(sum(row.get("correct") is True for row in valid), len(valid)) if valid else summary.get("accuracy_pct")
        latency_values = [row.get("latency_ms") for row in rows if isinstance(row.get("latency_ms"), (int, float))]
        latency = round(sum(latency_values) / len(latency_values)) if latency_values else summary.get("avg_latency_ms")
        values = (attack_success, detection, false_positive, accuracy)
        percentages = ["N/A" if value is None else f"{value:.1f}%" for value in values]
        errors = len(rows) - len(valid) if rows else summary.get("errors", 0)
        latency_text = "N/A" if latency is None else f"{latency} ms"
        print(f"{summary.get('model', '')[:42]:42s} {mode:16s} {input_mode:14s} {percentages[0]:15s} {percentages[1]:13s} {percentages[2]:10s} {percentages[3]:9s} {errors:6d} {latency_text}")
    prompt_config = comparison.get("prompt_config", {})
    print("\nAttack prompt methods: " + ", ".join(prompt_config.get("attack_prompt_ids", [])))
    print("Defense prompt methods: " + ", ".join(prompt_config.get("defense_prompt_ids", [])))
    print("Attack success = attacks not detected (a bypass). Defense rate = attacks detected as attacks.")


def main():
    parser = argparse.ArgumentParser(description="Run image prompt-injection baseline and model evaluations.")
    parser.add_argument("--corpus", default=DEFAULT_CORPUS)
    parser.add_argument("--image-set", help="Local folder, JSON manifest, or HTTP(S) JSON manifest")
    parser.add_argument("--max-samples", type=int, help="Limit each selected image set to this many samples")
    parser.add_argument("--prompt", help="Use one prompt for every image in the selected set")
    parser.add_argument("--models", help="Comma-separated provider:model values")
    parser.add_argument("--cpu-only", action="store_true", help="Run Ollama evaluation without GPU selection; defaults to the 8 GB profile when no model is supplied")
    parser.add_argument("--cpu-profile", choices=sorted(CPU_PROFILES), help="Choose a RAM profile: 8gb, 16gb, or more; recommends a model and safe sample limit")
    parser.add_argument("--image-models", action="store_true",
                        help="List catalog image models, show installed sizes, and offer to download missing Ollama models")
    parser.add_argument("--list-capabilities", action="store_true",
                        help="List all catalog models and attack/defense prompt methods")
    parser.add_argument("--capability-report", action="store_true",
                        help="Print attack success, defense, false-positive, accuracy, and error rates from the latest comparison")
    parser.add_argument("--quick-vision-test", action="store_true",
                        help="Embed all predefined attacks into images and compare installed vision models with and without defense")
    parser.add_argument("--combined-vision-test", action="store_true",
                        help="Run a short test using one image containing all predefined attack types plus one benign image")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--yes-download", action="store_true", help="Allow missing selected Ollama models to download (enabled by default)")
    parser.add_argument("--no-download", action="store_true", help="Fail instead of downloading missing selected Ollama models")
    parser.add_argument("--ocr-fallback", action="store_true",
                        help="Evaluate text-only models using the corpus OCR transcript instead of image bytes")
    parser.add_argument("--prompts-file", default=PROMPTS_PATH, help="JSON file containing attack and defense prompt libraries")
    parser.add_argument("--attack-prompt-id", help="Predefined attack prompt id")
    parser.add_argument("--custom-attack-prompt", help="Custom attack prompt; use {action} for the target action")
    parser.add_argument("--attack-action", default="send_alert('test')", help="Action substituted into the attack prompt")
    parser.add_argument("--overlay-attack-prompt", action="store_true", help="Render the attack prompt into attack-labeled images")
    parser.add_argument("--defense-mode", choices=["none", "defense", "both"], default="none",
                        help="Run without a model defense, with the defense layer, or both")
    parser.add_argument("--defense-prompt-id", help="Predefined defense prompt id")
    parser.add_argument("--custom-defense-prompt", help="Custom defense instruction added to the model system prompt")
    parser.add_argument("--overlay-dir", default=os.path.join(RESULTS_DIR, "prompt_overlays"), help="Output folder for generated overlays")
    parser.add_argument("--interactive", action="store_true", help="Open the terminal wizard for models, prompts, downloads, and defense modes")
    args = parser.parse_args()

    if args.list_capabilities:
        print_capability_list()
        return
    if args.capability_report:
        try:
            print_capability_report()
        except RuntimeError as exc:
            parser.error(str(exc))
        return

    if args.image_models:
        try:
            show_image_models(MODELS_PATH, args.yes_download)
        except RuntimeError as exc:
            parser.error(str(exc))
        return

    if args.interactive:
        selected = configure_interactive(MODELS_PATH, args.prompts_file)
        args.models = ",".join(selected["models"])
        args.ocr_models = selected["ocr_models"]
        args.attack_prompt_ids = selected["attack_ids"]
        args.defense_prompt_ids = selected["defense_ids"]
        args.defense_mode = selected["defense_mode"]
        args.overlay_attack_prompt = selected["overlay"]
        args.ocr_fallback = selected["ocr_fallback"]
        args.custom_attack_prompt = selected["attack_custom"] or None
        args.custom_defense_prompt = selected["defense_custom"] or None

    profile_name = args.cpu_profile or ("8gb" if args.cpu_only else None)
    if profile_name:
        profile = CPU_PROFILES[profile_name]
        os.environ["OLLAMA_NUM_GPU"] = "0"
        print(f"CPU-only profile {profile_name}: recommended {profile['model']}; max samples {profile['max_samples']}; timeout {profile['timeout']}s. {profile['note']}")
        if not args.models:
            args.models = profile["model"]
        if args.max_samples is None:
            args.max_samples = profile["max_samples"]
        if args.timeout == 60:
            args.timeout = profile["timeout"]

    with open(args.corpus, encoding="utf-8") as file:
        corpus = json.load(file)
    prompt_pack = load_pack(args.prompts_file)
    if args.quick_vision_test or args.combined_vision_test:
        if not args.models:
            args.models = ",".join(installed_vision_model_specs(MODELS_PATH))
        if not args.models:
            parser.error("No installed catalog vision models found. Run --image-models or install a vision model first.")
        args.attack_prompt_ids = ["combined_attacks"] if args.combined_vision_test else [entry["id"] for entry in prompt_pack.get("attack_prompts", [])]
        args.defense_prompt_ids = ["layered_defense"]
        args.defense_mode = "both"
        args.overlay_attack_prompt = True
        if args.combined_vision_test:
            args.custom_attack_prompt = combine_attack_prompts(prompt_pack, args.attack_action)
            print("Combined vision test: one attack image contains all predefined attack types, plus one benign control; running without and with layered_defense.")
        else:
            print("Quick vision test: predefined attacks will be embedded into image copies; running without and with layered_defense.")
    attack_prompt_ids = getattr(args, "attack_prompt_ids", None)
    if not attack_prompt_ids:
        attack_prompt_ids = [args.attack_prompt_id] if args.attack_prompt_id else [None]
    defense_prompt_ids = getattr(args, "defense_prompt_ids", None)
    if not defense_prompt_ids:
        defense_prompt_ids = [args.defense_prompt_id] if args.defense_prompt_id else [None]
    model_rows = []
    rows = []
    specs = parse_specs(args.models) if args.models else []
    if not specs and os.path.exists(MODELS_PATH):
        with open(MODELS_PATH, encoding="utf-8") as file:
            specs = json.load(file).get("selected_models", [])
    if specs:
        ensure_ollama_models(specs, args.yes_download or not args.no_download)
    for attack_index, attack_prompt_id in enumerate(attack_prompt_ids):
        samples = load_samples(corpus, args.image_set, args.prompt)
        if args.max_samples is not None:
            if args.max_samples < 1:
                parser.error("--max-samples must be at least 1")
            samples = samples[:args.max_samples]
        if args.combined_vision_test:
            attack_sample = next((sample for sample in samples if sample.get("label") == "attack"), None)
            benign_sample = next((sample for sample in samples if sample.get("label") == "benign"), None)
            samples = [sample for sample in (attack_sample, benign_sample) if sample]
        attack_prompt = None
        attack_definition = next((entry for entry in prompt_pack.get("attack_prompts", []) if entry.get("id") == attack_prompt_id), {})
        attack_prompt_name = attack_definition.get("name", "Custom attack" if args.custom_attack_prompt else "Corpus default")
        if attack_prompt_id or args.custom_attack_prompt or args.overlay_attack_prompt:
            attack_prompt = choose_attack_prompt(prompt_pack, attack_prompt_id, args.custom_attack_prompt, args.attack_action)
            if args.overlay_attack_prompt:
                overlay_prompt(samples, attack_prompt, os.path.join(args.overlay_dir, attack_prompt_id or "custom"), max_lines=40 if args.combined_vision_test else 8)
            else:
                for sample in samples:
                    if sample.get("label") == "attack":
                        sample["ocr_text"] = attack_prompt + "\n" + sample.get("ocr_text", "")
        if attack_index == 0:
            for sample in samples:
                undefended = run_undefended(sample.get("prompt", ""), sample.get("ocr_text", ""))
                defended = run_defended(sample.get("prompt", ""), sample.get("ocr_text", ""), inspect)
                attack = sample.get("label") == "attack"
                benign = sample.get("label") == "benign"
                rows.append({
                    "id": sample.get("id"), "category": sample.get("category", "external"), "label": sample.get("label", "unknown"),
                    "image": sample.get("image"), "image_available": bool(sample.get("image_bytes")), "image_error": sample.get("image_error", ""),
                    "attack_prompt_id": attack_prompt_id or "corpus_default", "attack_type": attack_prompt_name,
                    "injected_prompt": attack_prompt or sample.get("ocr_text", ""), "attack_action": args.attack_action,
                    "undefended_executed": undefended.executed, "undefended_tool_called": undefended.tool,
                    "undefended_attack_success": bool(attack and undefended.executed), "undefended_latency_ms": round(undefended.latency_ms, 4),
                    "defended_decision": defended.detector_decision, "defended_score": defended.detector_score,
                    "defended_matched_categories": ";".join(defended.detector_matches), "defended_executed": defended.executed,
                    "defended_attack_success": bool(attack and defended.executed), "defended_false_positive": bool(benign and defended.detector_decision in ("block", "hold")),
                    "defended_latency_ms": round(defended.latency_ms, 4),
                })
        if specs:
            modes = ["none", "defense"] if args.defense_mode == "both" else [args.defense_mode]
            for mode in modes:
                selected_defense_ids = defense_prompt_ids if mode == "defense" else [None]
                for defense_prompt_id in selected_defense_ids:
                    defense_prompt = choose_defense_prompt(prompt_pack, defense_prompt_id, args.custom_defense_prompt) if mode == "defense" else None
                    defense_definition = next((entry for entry in prompt_pack.get("defense_prompts", []) if entry.get("id") == defense_prompt_id), {})
                    defense_name = defense_definition.get("name", "Custom defense" if args.custom_defense_prompt else "None")
                    evaluated = evaluate(samples, specs, args.timeout, ocr_fallback=args.ocr_fallback,
                                          ocr_models=getattr(args, "ocr_models", None),
                                          defense_prompt=defense_prompt,
                                          defense_mode=mode if not defense_prompt_id else f"{mode}:{defense_prompt_id}")
                    for result in evaluated:
                        sample = next((item for item in samples if item.get("id") == result.get("id")), {})
                        result["attack_prompt_id"] = attack_prompt_id or "corpus_default"
                        result["attack_type"] = attack_prompt_name
                        result["injected_prompt"] = attack_prompt or sample.get("ocr_text", "")
                        result["attack_action"] = args.attack_action
                        result["defense_prompt_id"] = defense_prompt_id or "none"
                        result["defense_type"] = defense_name
                        result["defense_prompt"] = defense_prompt or ""
                        result["image"] = sample.get("image", "")
                        result["image_available"] = bool(sample.get("image_bytes"))
                        result["image_error"] = sample.get("image_error", "")
                    model_rows.extend(evaluated)

    attacks = [row for row in rows if row["label"] == "attack"]
    benign = [row for row in rows if row["label"] == "benign"]
    run_timestamp = datetime.datetime.now(datetime.timezone.utc)
    run_metadata = {"run_id": run_timestamp.strftime("%Y%m%dT%H%M%S%fZ"), "run_timestamp_utc": run_timestamp.isoformat(), "command": subprocess.list2cmdline([sys.executable] + sys.argv), "corpus": args.corpus, "image_set": args.image_set or "corpus default"}
    summary = {"corpus_version": corpus.get("corpus_version"), "scenario": corpus.get("scenario"), "run_timestamp_utc": run_metadata["run_timestamp_utc"], "python_version": platform.python_version(), "n_attack_samples": len(attacks), "n_benign_samples": len(benign), "n_image_errors": sum(not row["image_available"] for row in rows), "undefended": {"attack_success_rate_pct": _pct(sum(row["undefended_attack_success"] for row in attacks), len(attacks))}, "defended": {"attack_success_rate_pct": _pct(sum(row["defended_attack_success"] for row in attacks), len(attacks)), "false_positive_rate_pct": _pct(sum(row["defended_false_positive"] for row in benign), len(benign)), "attacks_blocked": sum(row["defended_decision"] == "block" for row in attacks), "attacks_held_for_review": sum(row["defended_decision"] == "hold" for row in attacks), "attacks_allowed": sum(row["defended_decision"] == "allow" for row in attacks)}}

    os.makedirs(RESULTS_DIR, exist_ok=True)
    _archive_results()
    with open(os.path.join(RESULTS_DIR, "results.json"), "w", encoding="utf-8") as file:
        json.dump({"run": run_metadata, "summary": summary, "rows": rows}, file, indent=2)
    with open(os.path.join(RESULTS_DIR, "results.csv"), "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)

    if specs:
        attack_prompts = []
        defense_prompts = []
        for result in model_rows:
            attack_record = {"id": result.get("attack_prompt_id"), "type": result.get("attack_type"), "text": result.get("injected_prompt")}
            defense_record = {"id": result.get("defense_prompt_id"), "type": result.get("defense_type"), "text": result.get("defense_prompt")}
            if attack_record not in attack_prompts:
                attack_prompts.append(attack_record)
            if defense_record not in defense_prompts:
                defense_prompts.append(defense_record)
        with open(os.path.join(RESULTS_DIR, "model_comparison.json"), "w", encoding="utf-8") as file:
            json.dump({"run": run_metadata, "models": summarize(model_rows), "rows": model_rows,
                       "prompt_config": {"defense_mode": args.defense_mode, "overlay_attack_prompt": args.overlay_attack_prompt,
                                          "attack_prompt_ids": attack_prompt_ids, "defense_prompt_ids": defense_prompt_ids,
                                          "attack_prompts": attack_prompts, "defense_prompts": defense_prompts,
                                          "command": run_metadata["command"]}}, file, indent=2)
        with open(os.path.join(RESULTS_DIR, "model_comparison.csv"), "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(model_rows[0].keys()))
            writer.writeheader(); writer.writerows(model_rows)
        report_script = os.path.join(os.path.dirname(__file__), "generate_reports.js")
        if os.path.exists(report_script):
            report_result = subprocess.run(["node", report_script], capture_output=True, text=True, check=False)
            if report_result.returncode:
                print("Report generation failed: " + (report_result.stderr.strip() or "unknown error"), file=sys.stderr)
            elif report_result.stdout.strip():
                print(report_result.stdout.strip())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()