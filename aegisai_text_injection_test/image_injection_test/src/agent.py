"""Undefended and defended image-review agent simulations."""

import re
import time
from dataclasses import dataclass, field

ACTION_RE = re.compile(r"\b(?:call|run|execute)\s+([a-z_][a-z0-9_]*)\s*\(", re.IGNORECASE)


@dataclass
class RunResult:
    executed: bool
    tool: str = None
    latency_ms: float = 0.0
    detector_score: float = None
    detector_decision: str = None
    detector_matches: list = field(default_factory=list)


def _action(text):
    match = ACTION_RE.search(text or "")
    return match.group(1) if match else None


def run_undefended(prompt, ocr_text):
    started = time.perf_counter()
    action = _action(prompt + "\n" + (ocr_text or ""))
    return RunResult(bool(action), action, (time.perf_counter() - started) * 1000)


def run_defended(prompt, ocr_text, inspect_fn):
    started = time.perf_counter()
    verdict = inspect_fn(ocr_text or "", prompt)
    if verdict.decision in ("block", "hold"):
        return RunResult(False, latency_ms=(time.perf_counter() - started) * 1000,
                         detector_score=verdict.score, detector_decision=verdict.decision,
                         detector_matches=verdict.matched)
    # OCR from the image is never a trusted command source.
    action = _action(prompt)
    return RunResult(bool(action), action, (time.perf_counter() - started) * 1000,
                     verdict.score, verdict.decision, verdict.matched)