"""Load built-in, local-folder, manifest, and HTTP image sets."""

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path

from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}


def _read_url(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read(), response.headers.get_content_type()


def _read_image(path_or_url, base_dir):
    if str(path_or_url).startswith(("http://", "https://")):
        data, mime = _read_url(path_or_url)
        if mime == "image/svg+xml":
            return _svg_to_png(data), "image/png"
        return data, mime
    path = Path(path_or_url)
    if not path.is_absolute():
        path = Path(base_dir) / path
    data = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if mime == "image/svg+xml":
        return _svg_to_png(data), "image/png"
    return data, mime


def _svg_to_png(data):
    drawing = svg2rlg(BytesIO(data))
    if drawing is None:
        raise ValueError("Unable to parse SVG image")
    output = BytesIO()
    renderPM.drawToFile(drawing, output, fmt="PNG")
    return output.getvalue()


def _manifest(source):
    if str(source).startswith(("http://", "https://")):
        data, _ = _read_url(source)
        return json.loads(data.decode("utf-8")), str(source).rsplit("/", 1)[0]
    path = Path(source)
    with path.open(encoding="utf-8") as file:
        return json.load(file), str(path.parent)


def load_samples(corpus, source=None, prompt_override=None):
    samples = [dict(sample) for sample in corpus.get("samples", [])]
    if source:
        path = Path(source) if not str(source).startswith(("http://", "https://")) else None
        if path and path.is_dir():
            labels = path / "labels.json"
            if labels.exists():
                samples, base_dir = _manifest(labels)
            else:
                samples = [{"id": p.stem, "image": p.name, "prompt": prompt_override or "Review this image for a prompt injection.", "label": "unknown", "category": "external"}
                           for p in sorted(path.iterdir()) if p.suffix.lower() in SUPPORTED]
                base_dir = str(path)
        else:
            samples, base_dir = _manifest(source)
    else:
        base_dir = str(Path(__file__).resolve().parent.parent / "corpus")

    loaded = []
    for sample in samples:
        item = dict(sample)
        item["prompt"] = prompt_override or item.get("prompt", "Review this image for a prompt injection.")
        try:
            item["image_bytes"], item["mime_type"] = _read_image(item["image"], base_dir)
            item["image_data_uri"] = "data:{};base64,{}".format(item["mime_type"], base64.b64encode(item["image_bytes"]).decode("ascii"))
            item["image_error"] = ""
        except (OSError, ValueError, urllib.error.URLError) as exc:
            item["image_bytes"] = None
            item["mime_type"] = ""
            item["image_data_uri"] = ""
            item["image_error"] = str(exc)
        loaded.append(item)
    return loaded