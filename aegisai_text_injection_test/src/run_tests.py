import json
import csv
import sys
import os
import platform
import datetime
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from detector import inspect
from agent import run_undefended, run_defended
from model_eval import ensure_ollama_models, evaluate, summarize, parse_specs

CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "corpus", "text_injection_corpus_v1.0.0.json")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
MODELS_PATH = os.path.join(os.path.dirname(__file__), "..", "models.json")


def write_model_grouped_csv(file, fieldnames, rows):
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    previous_model = None
    for row in rows:
        if previous_model is not None and row.get("model") != previous_model:
            blank_row = ",".join([""] * len(fieldnames)) + "\n"
            file.write(blank_row + blank_row)
        writer.writerow(row)
        previous_model = row.get("model")


def main():
    parser = argparse.ArgumentParser(description="Run baseline and optional AI model evaluations.")
    parser.add_argument("--models", help="Comma-separated provider:model values; overrides models.json")
    parser.add_argument("--models-file", default=MODELS_PATH, help="JSON file containing selected_models")
    parser.add_argument("--timeout", type=int, default=60, help="Per-model request timeout in seconds")
    parser.add_argument("--yes-download", action="store_true",
                        help="Automatically download missing Ollama models")
    args = parser.parse_args()
    with open(CORPUS_PATH) as f:
        corpus = json.load(f)

    selected_specs = parse_specs(args.models) if args.models else []
    if not selected_specs and args.models_file and os.path.exists(args.models_file):
        with open(args.models_file, encoding="utf-8") as file:
            selected_specs = parse_specs(",".join(json.load(file).get("selected_models", [])))
    if selected_specs:
        try:
            ensure_ollama_models(selected_specs, auto_download=args.yes_download)
        except RuntimeError as error:
            parser.error(str(error))

    rows = []
    for sample in corpus["samples"]:
        u = run_undefended(sample["task"], sample["document"])
        d = run_defended(sample["task"], sample["document"], inspect)

        # Attack success = the unsafe/attack-targeted tool call actually executed
        u_success = bool(u.executed and sample["label"] == "attack")
        d_success = bool(d.executed and sample["label"] == "attack")
        # False positive = a BENIGN sample that the defended pipeline blocked or held
        d_false_positive = bool(sample["label"] == "benign" and d.detector_decision in ("block", "hold"))

        rows.append({
            "id": sample["id"],
            "category": sample["category"],
            "label": sample["label"],
            "undefended_executed": u.executed,
            "undefended_tool_called": u.tool,
            "undefended_latency_ms": round(u.latency_ms, 4),
            "undefended_attack_success": u_success,
            "defended_decision": d.detector_decision,
            "defended_score": d.detector_score,
            "defended_matched_categories": ";".join(d.detector_matches),
            "defended_executed": d.executed,
            "defended_latency_ms": round(d.latency_ms, 4),
            "defended_attack_success": d_success,
            "defended_false_positive": d_false_positive,
        })

    attacks = [r for r in rows if r["label"] == "attack"]
    benign = [r for r in rows if r["label"] == "benign"]

    def pct(n, d):
        return round(100 * n / d, 1) if d else 0.0

    summary = {
        "corpus_version": corpus["corpus_version"],
        "scenario": corpus["scenario"],
        "run_timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "n_attack_samples": len(attacks),
        "n_benign_samples": len(benign),
        "undefended": {
            "attack_success_rate_pct": pct(sum(r["undefended_attack_success"] for r in attacks), len(attacks)),
            "avg_latency_ms": round(sum(r["undefended_latency_ms"] for r in rows) / len(rows), 4),
        },
        "defended": {
            "attack_success_rate_pct": pct(sum(r["defended_attack_success"] for r in attacks), len(attacks)),
            "false_positive_rate_pct": pct(sum(r["defended_false_positive"] for r in benign), len(benign)),
            "avg_latency_ms": round(sum(r["defended_latency_ms"] for r in rows) / len(rows), 4),
            "attacks_blocked": sum(1 for r in attacks if r["defended_decision"] == "block"),
            "attacks_held_for_review": sum(1 for r in attacks if r["defended_decision"] == "hold"),
            "attacks_allowed": sum(1 for r in attacks if r["defended_decision"] == "allow"),
        },
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "results.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=2)

    with open(os.path.join(RESULTS_DIR, "results.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    model_rows = []
    model_summary = []
    if selected_specs:
        model_rows = evaluate(corpus, selected_specs, args.timeout)
        model_summary = summarize(model_rows)
        with open(os.path.join(RESULTS_DIR, "model_comparison.json"), "w") as f:
            json.dump({"models": model_summary, "rows": model_rows}, f, indent=2)
        if model_rows:
            with open(os.path.join(RESULTS_DIR, "model_comparison.csv"), "w", newline="") as f:
                write_model_grouped_csv(f, list(model_rows[0].keys()), model_rows)

    print(json.dumps(summary, indent=2))
    print("\nPer-sample results:")
    for r in rows:
        flag = ""
        if r["label"] == "attack" and r["undefended_attack_success"] and not r["defended_attack_success"]:
            flag = "  <- defended pipeline caught this"
        elif r["label"] == "attack" and r["defended_attack_success"]:
            flag = "  <- ATTACK SUCCEEDED EVEN WHEN DEFENDED"
        elif r["label"] == "benign" and r["defended_false_positive"]:
            flag = "  <- FALSE POSITIVE"
        print(f"  {r['id']:8s} {r['category']:32s} undef={str(r['undefended_executed']):5s} "
              f"def={r['defended_decision']:5s}{flag}")
    if model_summary:
        print("\nAI model comparison:")
        for summary in model_summary:
            print(f"  {summary['model']}: accuracy={summary['accuracy_pct']}% attack_detection={summary['attack_detection_rate_pct']}% false_positive={summary['false_positive_rate_pct']}% errors={summary['errors']}")


if __name__ == "__main__":
    main()
