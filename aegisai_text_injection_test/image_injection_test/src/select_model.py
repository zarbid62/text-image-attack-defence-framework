import argparse
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
CONFIG_PATH = os.path.join(ROOT, "models.json")


def load():
    with open(CONFIG_PATH, encoding="utf-8") as file:
        return json.load(file)


def save(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2); file.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Manage image-evaluation models")
    parser.add_argument("command", choices=["list", "select", "add", "remove"], nargs="?", default="list")
    parser.add_argument("value", nargs="?")
    args = parser.parse_args(); config = load(); selected = set(config.get("selected_models", []))
    if args.command == "list":
        for number, model in enumerate(config.get("catalog", []), 1):
            print("{} {:2d}. {} [{}]".format("*" if model["id"] in selected else " ", number, model["name"], model["id"]))
        print("\nSelected: " + ", ".join(config.get("selected_models", [])) or "none")
    elif args.command == "select":
        indexes = [int(value.strip()) for value in (args.value or "").split(",") if value.strip()]
        config["selected_models"] = [config["catalog"][index - 1]["id"] for index in indexes]; save(config); main_list(config)
    elif args.command in {"add", "remove"}:
        if not args.value or ":" not in args.value: raise SystemExit("Use provider:model")
        values = config.setdefault("selected_models", [])
        if args.command == "add" and args.value not in values: values.append(args.value)
        if args.command == "remove": config["selected_models"] = [value for value in values if value != args.value]
        save(config)


def main_list(config):
    print("Selected: " + ", ".join(config.get("selected_models", [])) or "none")


if __name__ == "__main__":
    main()