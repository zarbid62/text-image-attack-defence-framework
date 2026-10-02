"""Interactive terminal wizard for image-injection evaluations."""

import json
import os
import subprocess


def _ask(message, default=""):
    answer = input(f"{message}{' [' + default + ']' if default else ''}: ").strip()
    return answer or default


def _ollama_inventory():
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
    except OSError as exc:
        raise RuntimeError("Ollama is not installed or unavailable on PATH") from exc
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Ollama is unavailable")
    inventory = {}
    for line in result.stdout.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 3:
            inventory[fields[0]] = " ".join(fields[2:4])
            if fields[0].endswith(":latest"):
                inventory[fields[0][:-7]] = inventory[fields[0]]
    return inventory


def _catalog(models_path):
    with open(models_path, encoding="utf-8") as file:
        return json.load(file).get("catalog", [])


def _download_selected(entries, installed, title):
    selected = [entry["id"] for entry in entries]
    missing = [entry for entry in entries if entry["id"].split(":", 1)[1] not in installed]
    if not missing:
        return selected
    print(f"\nSelected {title} models not installed:")
    for entry in missing:
        name = entry["id"].split(":", 1)[1]
        print(f"  {name} ({entry.get('download_size', 'size shown by Ollama during pull')})")
    if _ask("Download selected missing models now? y/n", "y").lower() not in {"y", "yes"}:
        raise RuntimeError("Model download cancelled")
    for entry in missing:
        name = entry["id"].split(":", 1)[1]
        print(f"Downloading {name}...")
        if subprocess.run(["ollama", "pull", name], check=False).returncode:
            raise RuntimeError(f"Failed to download Ollama model: {name}")
    return selected


def choose_model_group(models_path, vision, title):
    catalog = [entry for entry in _catalog(models_path)
               if entry.get("provider", "ollama") == "ollama" and bool(entry.get("vision")) == vision]
    installed = _ollama_inventory()
    print(f"\n{title} models (type skip to skip this group):")
    for number, entry in enumerate(catalog, 1):
        name = entry["id"].split(":", 1)[1]
        status = f"installed, {installed[name]}" if name in installed else "not installed"
        size = installed.get(name, entry.get("download_size", "size shown during pull"))
        print(f"  {number:2d}. {name:24s} ({status}; {size})")
    while True:
        selection = _ask("Enter model number(s), comma-separated", "skip").lower()
        if selection in {"skip", "s", "none", "n"}:
            return []
        try:
            indexes = [int(value.strip()) for value in selection.split(",") if value.strip()]
            if not indexes or any(index < 1 or index > len(catalog) for index in indexes):
                raise ValueError
            break
        except ValueError:
            print("Use valid numbers such as 1,2,3, or type skip.")
    return _download_selected([catalog[index - 1] for index in dict.fromkeys(indexes)], installed, title)


def choose_models(models_path):
    vision_models = choose_model_group(models_path, True, "Actual image vision")
    ocr_models = choose_model_group(models_path, False, "OCR fallback")
    return vision_models + ocr_models, ocr_models


def choose_prompt_ids(pack, key, label):
    entries = pack.get(key, [])
    print(f"\nAvailable {label} prompts:")
    for number, entry in enumerate(entries, 1):
        print(f"  {number:2d}. {entry['id']:20s} {entry['name']}")
    count = _ask(f"How many {label} prompts", "1").lower()
    if count == "all":
        count_value = len(entries)
    else:
        count_value = max(1, min(len(entries), int(count)))
    while True:
        selection = _ask(f"Choose {count_value} {label} prompt number(s)")
        indexes = [int(value.strip()) for value in selection.split(",") if value.strip()]
        if len(indexes) == count_value and all(1 <= index <= len(entries) for index in indexes):
            return [entries[index - 1]["id"] for index in dict.fromkeys(indexes)]
        print(f"Choose exactly {count_value} valid numbers.")


def configure(models_path, prompts_path):
    with open(prompts_path, encoding="utf-8") as file:
        pack = json.load(file)
    models, ocr_models = choose_models(models_path)
    attack_ids = choose_prompt_ids(pack, "attack_prompts", "attack")
    defense_ids = choose_prompt_ids(pack, "defense_prompts", "defense")
    defense_mode = _ask("Run without defense, with defense, or both (none/defense/both)", "both").lower()
    while defense_mode not in {"none", "defense", "both"}:
        defense_mode = _ask("Enter none, defense, or both", "both").lower()
    overlay = _ask("Render selected attack prompts into attack images? y/n", "y").lower() in {"y", "yes"}
    return {"models": models, "ocr_models": ocr_models, "attack_ids": attack_ids, "defense_ids": defense_ids,
            "defense_mode": defense_mode, "overlay": overlay, "ocr_fallback": False,
            "attack_custom": _ask("Optional custom attack prompt, blank for selected library prompts"),
            "defense_custom": _ask("Optional custom defense prompt, blank for selected library prompts")}
