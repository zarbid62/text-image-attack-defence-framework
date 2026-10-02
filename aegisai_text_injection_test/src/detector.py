"""
Heuristic text-based prompt-injection detector.

This is a rule-based PROTOTYPE for the text slice of AegisAI's "Interception 1:
Content Inspection" stage (FYDP-1 report, Section 3.2, Figure 3.4). It is not the
final detector: FYDP-2 (P6, Table 3.4) implements the full image/hybrid/tool/auth
detectors behind a common verdict interface. This module exists so the corpus and
evaluation pipeline (FR-11, NFR-6) can be exercised and reported on now, ahead of
that work, using a transparent, reproducible ruleset.

Score-based verdict, mirroring the two-threshold pipeline described in Section 3.2:
  score <  LOW_THRESHOLD   -> allow
  LOW <= score < HIGH      -> hold (escalate to human reviewer)
  score >= HIGH_THRESHOLD  -> block
"""

import re
from dataclasses import dataclass, field

LOW_THRESHOLD = 2.0
HIGH_THRESHOLD = 4.0

# Each pattern: (regex, weight, category label for the audit log)
PATTERNS = [
    (r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions?\b", 3.0, "instruction_override"),
    (r"\bdisregard\s+(all\s+)?(previous|prior|above)\b", 3.0, "instruction_override"),
    (r"\byou are now\b", 2.0, "role_reassignment"),
    (r"\boverride\s+mode\b|\bpriority override\b|\bmaintenance override\b", 2.5, "override_claim"),
    (r"\[\s*(system|admin)\s*\]", 3.0, "forged_role_tag"),
    (r"---\s*(end of document|operator instruction)", 3.0, "delimiter_escape"),
    (r"\bnew directive\b|\bplant administrator\b", 2.0, "authority_impersonation"),
    (r"\bpretend you are\b|\bin this fictional mode\b|\bhypothetically\b", 2.0, "roleplay_jailbreak"),
    (r"\bskip all confirmation\b|\bno time to verify\b|\bno need to check\b", 2.5, "safety_bypass_pretext"),
    (r"\bnext_action\s*:\s*call\b", 3.0, "fake_tool_response_instruction"),
    (r"\bdecode and follow\b", 3.0, "encoded_instruction"),
    (r"[A-Za-z0-9+/]{24,}={0,2}", 1.0, "possible_base64_blob"),
    (r"\bfrom now on\b.{0,40}\b(treat|trust)\b", 2.5, "policy_priming"),
    (r"\bcall\s+(write_setpoint|send_email|export_process_log|send_alert)\s*\(", 1.5, "embedded_tool_call_syntax"),
    (r"\bexternal[-_]?(relay|host|mirror)\b|\bfreemailbox\.com\b|@[\w.-]+\.(io|net)\b", 1.5, "suspicious_destination"),
]

COMPILED = [(re.compile(p, re.IGNORECASE), w, cat) for p, w, cat in PATTERNS]


@dataclass
class Verdict:
    score: float
    decision: str  # "allow" | "hold" | "block"
    matched: list = field(default_factory=list)


def inspect(text: str) -> Verdict:
    score = 0.0
    matched = []
    for regex, weight, category in COMPILED:
        hits = regex.findall(text)
        if hits:
            score += weight
            matched.append(category)
    if score >= HIGH_THRESHOLD:
        decision = "block"
    elif score >= LOW_THRESHOLD:
        decision = "hold"
    else:
        decision = "allow"
    return Verdict(score=round(score, 2), decision=decision, matched=matched)
