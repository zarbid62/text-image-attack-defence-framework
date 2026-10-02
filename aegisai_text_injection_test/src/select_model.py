"""Manage the models used by run_tests.py.

Examples:
  python src/select_model.py list
  python src/select_model.py select 1,2,3
  python src/select_model.py add ollama:my-model
  python src/select_model.py remove ollama:my-model
"""

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
CONFIG_PATH = os.path.join(ROOT, "models.json")


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as file:
        return json.load(file)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)
        file.write("\n")


def list_models(config):
    selected = set(config.get("selected_models", []))
    for number, model in enumerate(config.get("catalog", []), 1):
        marker = "*" if model["id"] in selected else " "
        key_status = "key" if model.get("requires_api_key") else "no-key"
        print(f"{marker} {number:2d}. {model['name']} [{model['id']}] ({key_status})")
    print(f"\nSelected ({len(selected)}): {', '.join(config.get('selected_models', [])) or 'none'}")


def add_model(config, model_id):
    if ":" not in model_id:
        raise ValueError("Use provider:model syntax, for example ollama:qwen2.5:0.5b")
    if model_id not in config.setdefault("selected_models", []):
        config["selected_models"].append(model_id)
    save_config(config)
    print(f"Added: {model_id}")


def main():
    parser = argparse.ArgumentParser(description="Select one or more models for the AegisAI test run.")
    parser.add_argument("command", choices=["list", "select", "add", "remove", "ollama"], nargs="?", default="list")
    parser.add_argument("values", nargs="?", help="Indexes for select, or a provider:model value")
    args = parser.parse_args()
    config = load_config()

    if args.command == "list":
        list_models(config)
    elif args.command == "select":
        if not args.values:
            raise SystemExit("select requires indexes, for example: select 1,2,3")
        catalog = config.get("catalog", [])
        indexes = [int(value.strip()) for value in args.values.split(",")]
        config["selected_models"] = [catalog[index - 1]["id"] for index in indexes]
        save_config(config)
        list_models(config)
    elif args.command == "add":
        if not args.values:
            raise SystemExit("add requires provider:model")
        add_model(config, args.values)
    elif args.command == "remove":
        if not args.values:
            raise SystemExit("remove requires provider:model")
        config["selected_models"] = [model for model in config.get("selected_models", []) if model != args.values]
        save_config(config)
        list_models(config)
    elif args.command == "ollama":
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        if result.returncode:
            print(result.stderr.strip() or "Ollama is not available.")
            return result.returncode
        print(result.stdout.rstrip())
        print("\nUse the model NAME with: python src/select_model.py add ollama:<NAME>")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, IndexError) as error:
        raise SystemExit(str(error))