"""Prompt packs and optional attack overlays for image evaluation."""

import base64
import json
import textwrap
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_pack(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def _find(entries, prompt_id, kind):
    for entry in entries:
        if entry["id"] == prompt_id:
            return entry["template"]
    raise ValueError(f"Unknown {kind} prompt id: {prompt_id}")


def choose_attack_prompt(pack, prompt_id=None, custom_prompt=None, action="send_alert('test')"):
    prompt_id = prompt_id or pack.get("defaults", {}).get("attack_prompt_id")
    template = custom_prompt or _find(pack.get("attack_prompts", []), prompt_id, "attack")
    return template.replace("{action}", action)


def choose_defense_prompt(pack, prompt_id=None, custom_prompt=None):
    prompt_id = prompt_id or pack.get("defaults", {}).get("defense_prompt_id")
    return custom_prompt or _find(pack.get("defense_prompts", []), prompt_id, "defense")


def combine_attack_prompts(pack, action="send_alert('test')"):
    sections = []
    for entry in pack.get("attack_prompts", []):
        text = entry["template"].replace("{action}", action)
        sections.append(f"[{entry['name'].upper()}]\n{text}")
    return "\n\n".join(sections)


def _overlay_raster(data, prompt, max_lines=8):
    image = Image.open(BytesIO(data)).convert("RGB")
    lines = textwrap.wrap(prompt, width=70)[:max_lines]
    height = 64 + len(lines) * 24
    canvas = Image.new("RGB", (image.width, image.height + height), "#8b1e3f")
    canvas.paste(image, (0, height))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((18, 14), "UNTRUSTED IMAGE TEXT", fill="#ffd166", font=font)
    for index, line in enumerate(lines):
        draw.text((18, 38 + index * 24), line, fill="white", font=font)
    output = BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue(), "image/png", ".png"


def _overlay_svg(data, prompt, max_lines=8):
    source = data.decode("utf-8")
    lines = textwrap.wrap(prompt, width=60)[:max_lines]
    escaped = [line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for line in lines]
    text = "".join(f'<text x="28" y="{42 + index * 22}" font-family="sans-serif" font-size="16" fill="white">{line}</text>' for index, line in enumerate(escaped))
    overlay = f'<rect x="10" y="10" width="880" height="{65 + len(lines) * 22}" fill="#8b1e3f" fill-opacity="0.94"/><text x="28" y="30" font-family="sans-serif" font-size="14" fill="#ffd166">UNTRUSTED IMAGE TEXT</text>{text}'
    return source.replace("</svg>", overlay + "</svg>").encode("utf-8"), "image/svg+xml", ".svg"


def overlay_prompt(samples, prompt, output_dir, max_lines=8):
    """Render an attack prompt into each loaded image and refresh image bytes."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for sample in samples:
        if sample.get("label") == "benign":
            continue
        data = sample.get("image_bytes")
        if not data:
            continue
        if sample.get("mime_type") == "image/svg+xml":
            rendered, mime_type, suffix = _overlay_svg(data, prompt, max_lines)
        else:
            rendered, mime_type, suffix = _overlay_raster(data, prompt, max_lines)
        target = output_dir / f"{sample['id']}_attack{suffix}"
        target.write_bytes(rendered)
        sample["image"] = str(target)
        sample["image_bytes"] = rendered
        sample["mime_type"] = mime_type
        sample["image_data_uri"] = "data:{};base64,{}".format(mime_type, base64.b64encode(rendered).decode("ascii"))
        sample["ocr_text"] = prompt + "\n" + sample.get("ocr_text", "")
    return samples
