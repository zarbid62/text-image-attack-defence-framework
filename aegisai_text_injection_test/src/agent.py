"""
Simulated industrial maintenance agent.

Scope note (important for the write-up): this is a rule-based STAND-IN for the
CrewAI/LangGraph agent that FYDP-1 Section 1.4 and Table 3.4 (P4, FYDP-2) specify
as the real testbed. A real LLM-driven agent is not yet built. This simulator
exists to make the text-injection corpus (FR-11) and the detector (Interception 1)
testable and reproducible now, with deterministic, explainable behaviour, while
the real agent testbed is built in FYDP-2. Results here characterize the CORPUS
and the DETECTOR RULESET, not the eventual LLM-driven agent's semantic judgment;
Section "Limitations" in the report makes this explicit.

Undefended baseline: naively scans the ENTIRE combined context (operator task +
untrusted document) for tool-call-shaped instructions and executes the first one
it finds outside the task field, exactly the failure mode described in FYDP-1
Section 1.1/1.2 ("part of its input ... is treated as data to reason over or act
on, and an attacker who controls any part of that data can attempt to redirect
the agent's plan").

Defended pipeline: mirrors Figure 3.4's Interception 1 + Interception 3.
  1. Run the content detector on the untrusted document.
  2. block  -> refuse the call, log verdict, nothing executed.
  3. hold   -> escalate to the review queue (NFR-8); for ASR purposes this counts
              as "not executed automatically", matching Section 3.2's decision
              pipeline (only 'allow' calls execute without a human).
  4. allow  -> baseline check (FR-6): only execute a tool call that is present in
              the TRUSTED task field. Content in the untrusted document is never
              treated as an instruction, regardless of detector outcome.
"""

import re
import time
from dataclasses import dataclass, field

TOOL_CALL_RE = re.compile(
    r"\b(write_setpoint|send_email|export_process_log|send_alert)\s*\(([^)]*)\)",
    re.IGNORECASE,
)


@dataclass
class RunResult:
    executed: bool
    tool: str = None
    arg: str = None
    latency_ms: float = 0.0
    detector_score: float = None
    detector_decision: str = None
    detector_matches: list = field(default_factory=list)


def _find_tool_call(text: str):
    m = TOOL_CALL_RE.search(text)
    if not m:
        return None, None
    return m.group(1), m.group(2).strip().strip("'\"")


def run_undefended(task: str, document: str) -> RunResult:
    start = time.perf_counter()
    combined = task + "\n" + document
    tool, arg = _find_tool_call(combined)
    latency = (time.perf_counter() - start) * 1000
    if tool:
        return RunResult(executed=True, tool=tool, arg=arg, latency_ms=latency)
    return RunResult(executed=False, latency_ms=latency)


def run_defended(task: str, document: str, inspect_fn) -> RunResult:
    start = time.perf_counter()
    verdict = inspect_fn(document)
    if verdict.decision in ("block", "hold"):
        latency = (time.perf_counter() - start) * 1000
        return RunResult(
            executed=False,
            latency_ms=latency,
            detector_score=verdict.score,
            detector_decision=verdict.decision,
            detector_matches=verdict.matched,
        )
    # allow: only trust the operator task field for tool calls (FR-6 baseline check)
    tool, arg = _find_tool_call(task)
    latency = (time.perf_counter() - start) * 1000
    if tool:
        return RunResult(
            executed=True, tool=tool, arg=arg, latency_ms=latency,
            detector_score=verdict.score, detector_decision=verdict.decision,
            detector_matches=verdict.matched,
        )
    return RunResult(
        executed=False, latency_ms=latency,
        detector_score=verdict.score, detector_decision=verdict.decision,
        detector_matches=verdict.matched,
    )
