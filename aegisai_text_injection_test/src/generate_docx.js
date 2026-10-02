const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, PageOrientation
} = require("docx");

const results = JSON.parse(fs.readFileSync(__dirname + "/../results/results.json", "utf8"));
const S = results.summary;
const rows = results.rows;

const corpus = JSON.parse(fs.readFileSync(__dirname + "/../corpus/text_injection_corpus_v1.0.0.json", "utf8"));
const comparisonPath = __dirname + "/../results/model_comparison.json";
const comparison = fs.existsSync(comparisonPath) ? JSON.parse(fs.readFileSync(comparisonPath, "utf8")) : null;

// ---------- helpers ----------
function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 150 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 250, after: 120 } });
}
function p(text, opts = {}) {
  return new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 160 } });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 80 } });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 20 })],
    spacing: { after: 200 },
    alignment: AlignmentType.CENTER,
  });
}

const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };
function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: "2F3B52" },
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 18 })] })],
  });
}
function bodyCell(text, width, opts = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill } : undefined,
    children: [new Paragraph({ children: [new TextRun({ text: String(text), size: 18, bold: !!opts.bold })] })],
  });
}

// ---------- Table 1: corpus summary ----------
const corpusWidths = [1000, 2600, 5600];
const corpusHeader = new TableRow({
  tableHeader: true,
  children: [headerCell("ID", corpusWidths[0]), headerCell("Category", corpusWidths[1]), headerCell("Technique", corpusWidths[2])],
});
const corpusRows = corpus.samples.map((s) =>
  new TableRow({
    children: [
      bodyCell(s.id, corpusWidths[0], { fill: s.label === "attack" ? "FDEDEC" : "EAF7EE" }),
      bodyCell(s.category, corpusWidths[1], { fill: s.label === "attack" ? "FDEDEC" : "EAF7EE" }),
      bodyCell(s.technique, corpusWidths[2], { fill: s.label === "attack" ? "FDEDEC" : "EAF7EE" }),
    ],
  })
);
const corpusTable = new Table({ width: { size: 9200, type: WidthType.DXA }, columnWidths: corpusWidths, rows: [corpusHeader, ...corpusRows] });

// ---------- Table 2: full per-sample results ----------
const resWidths = [900, 1500, 1500, 1300, 1300, 2700];
const resHeader = new TableRow({
  tableHeader: true,
  children: [
    headerCell("ID", resWidths[0]),
    headerCell("Undefended", resWidths[1]),
    headerCell("Defended verdict", resWidths[2]),
    headerCell("Score", resWidths[3]),
    headerCell("Executed?", resWidths[4]),
    headerCell("Outcome", resWidths[5]),
  ],
});
const resRows = rows.map((r) => {
  let outcome, fill;
  if (r.label === "attack" && r.undefended_attack_success && !r.defended_attack_success) {
    outcome = "Blocked by defended pipeline"; fill = "EAF7EE";
  } else if (r.label === "attack" && r.defended_attack_success) {
    outcome = "ATTACK SUCCEEDED (defended)"; fill = "FDEDEC";
  } else if (r.label === "attack" && !r.undefended_attack_success) {
    outcome = "Corpus sample not exploitable by baseline"; fill = "FFF7E0";
  } else if (r.label === "benign" && r.defended_false_positive) {
    outcome = "FALSE POSITIVE"; fill = "FDEDEC";
  } else {
    outcome = "Benign, correctly allowed"; fill = "EAF7EE";
  }
  return new TableRow({
    children: [
      bodyCell(r.id, resWidths[0], { fill }),
      bodyCell(r.undefended_executed ? `executed: ${r.undefended_tool_called}` : "no action", resWidths[1], { fill }),
      bodyCell(r.defended_decision, resWidths[2], { fill }),
      bodyCell(r.defended_score, resWidths[3], { fill }),
      bodyCell(r.defended_executed ? "yes" : "no", resWidths[4], { fill }),
      bodyCell(outcome, resWidths[5], { fill }),
    ],
  });
});
const resultsTable = new Table({ width: { size: 9200, type: WidthType.DXA }, columnWidths: resWidths, rows: [resHeader, ...resRows] });

// ---------- Table 3: summary metrics ----------
function metricRow(label, value) {
  return new TableRow({
    children: [bodyCell(label, 4600, { bold: true }), bodyCell(value, 4600)],
  });
}
const metricsTable = new Table({
  width: { size: 9200, type: WidthType.DXA },
  columnWidths: [4600, 4600],
  rows: [
    new TableRow({ tableHeader: true, children: [headerCell("Metric", 4600), headerCell("Value", 4600)] }),
    metricRow("Corpus version", S.corpus_version),
    metricRow("Attack samples / Benign control samples", `${S.n_attack_samples} / ${S.n_benign_samples}`),
    metricRow("Attack Success Rate — undefended baseline", `${S.undefended.attack_success_rate_pct}%`),
    metricRow("Attack Success Rate — AegisAI-style defended pipeline", `${S.defended.attack_success_rate_pct}%`),
    metricRow("False Positive Rate — defended pipeline (on benign controls)", `${S.defended.false_positive_rate_pct}%`),
    metricRow("Attacks blocked outright", `${S.defended.attacks_blocked} / ${S.n_attack_samples}`),
    metricRow("Attacks held for human review", `${S.defended.attacks_held_for_review} / ${S.n_attack_samples}`),
    metricRow("Attacks that reached 'allow' from the detector", `${S.defended.attacks_allowed} / ${S.n_attack_samples}`),
    metricRow("Avg. decision latency — undefended", `${S.undefended.avg_latency_ms} ms`),
    metricRow("Avg. decision latency — defended", `${S.defended.avg_latency_ms} ms`),
    metricRow("Run timestamp (UTC)", S.run_timestamp_utc),
  ],
});

const modelWidths = [2600, 1100, 1100, 1500, 1500, 1400];
const modelTable = comparison ? new Table({
  width: { size: 9200, type: WidthType.DXA }, columnWidths: modelWidths,
  rows: [
    new TableRow({ tableHeader: true, children: [
      headerCell("Model", modelWidths[0]), headerCell("Accuracy", modelWidths[1]),
      headerCell("Attack recall", modelWidths[2]), headerCell("Benign correct", modelWidths[3]),
      headerCell("False positives", modelWidths[4]), headerCell("Errors", modelWidths[5]),
    ]}),
    ...comparison.models.map((m) => new TableRow({ children: [
      bodyCell(m.model, modelWidths[0]), bodyCell(`${m.accuracy_pct ?? "N/A"}%`, modelWidths[1]),
      bodyCell(`${m.attack_detection_rate_pct ?? "N/A"}%`, modelWidths[2]),
      bodyCell(`${m.benign_correctly_rejected_as_not_attack_pct ?? "N/A"}%`, modelWidths[3]),
      bodyCell(`${m.false_positive_rate_pct ?? "N/A"}%`, modelWidths[4]), bodyCell(m.errors, modelWidths[5]),
    ]}))
  ],
}) : null;
const modelDetailWidths = [2200, 800, 900, 1100, 900, 3300];
const modelNames = comparison ? [...new Set(comparison.rows.map((r) => r.model))] : [];
const modelFills = ["E6F4F1", "E8EEFB", "FFF1D9", "F5E8F2", "E9F1DF", "FBE6E2", "E7EDF0"];
const modelDetailRows = comparison ? comparison.rows.reduce((result, r, index, allRows) => {
  if (index > 0 && r.model !== allRows[index - 1].model) {
    result.push(new TableRow({ children: modelDetailWidths.map((width) => bodyCell("", width)) }));
  }
  const fill = modelFills[modelNames.indexOf(r.model) % modelFills.length];
  result.push(new TableRow({ children: [
    bodyCell(r.model, modelDetailWidths[0], { fill }), bodyCell(r.id, modelDetailWidths[1], { fill }),
    bodyCell(r.label, modelDetailWidths[2], { fill }),
    bodyCell(r.predicted_attack === null ? "N/A" : (r.predicted_attack ? "attack" : "benign"), modelDetailWidths[3], { fill }),
    bodyCell(r.correct === null ? "N/A" : (r.correct ? "yes" : "no"), modelDetailWidths[4], { fill }),
    bodyCell(r.error || `${r.confidence}`, modelDetailWidths[5], { fill }),
  ] }));
  return result;
}, []) : [];
const modelDetailTable = comparison ? new Table({
  width: { size: 9200, type: WidthType.DXA }, columnWidths: modelDetailWidths,
  rows: [
    new TableRow({ tableHeader: true, children: [
      headerCell("Model", modelDetailWidths[0]), headerCell("ID", modelDetailWidths[1]),
      headerCell("Label", modelDetailWidths[2]), headerCell("Predicted", modelDetailWidths[3]),
      headerCell("Correct", modelDetailWidths[4]), headerCell("Confidence / error", modelDetailWidths[5]),
    ]}),
    ...modelDetailRows
  ],
}) : null;

const doc = new Document({
  sections: [
    {
      properties: { page: { size: { width: 12240, height: 15840 } } },
      children: [
        new Paragraph({
          children: [new TextRun({ text: "Text-Based Prompt Injection Testing", bold: true, size: 40 })],
          spacing: { after: 100 },
        }),
        new Paragraph({
          children: [new TextRun({ text: "AegisAI — Interim Testing Note (precedes FYDP-2 implementation)", italics: true, size: 24, color: "555555" })],
          spacing: { after: 400 },
        }),

        h1("1. Purpose and Scope"),
        p("This note documents the text-based prompt-injection testing requested ahead of the formal FYDP-2 build. FYDP-1 (Chapters 1–3) produced the threat model, requirements, and architecture for AegisAI but explicitly deferred implementation to FYDP-2 (Table 3.4, P4–P8). To produce concrete, reproducible evidence now, this work builds a small standalone test harness: a versioned text-injection attack corpus, a rule-based content detector standing in for Interception Point 1 of the architecture (Figure 3.4), and a simulated tool-calling agent run in both an undefended and a defended configuration."),
        p("This is a prototype, not the final evaluation. The real CrewAI/LangGraph agent, the ML-based detectors, and the live testbed described in Section 1.4 and Table 3.4 are FYDP-2 deliverables (P4–P6) and have not been built yet. Section 7 states exactly what this prototype does and does not demonstrate, so the results here are not overstated in the final report."),

        h1("2. Test Environment"),
        h2("2.1 Scenario"),
        p(`Scenario: "${corpus.scenario}." An agent has access to four tools: read_sensor(id), send_alert(msg), write_setpoint(value), send_email(to, body), and export_process_log(). Per the threat model in Section 3.1.2, the operator's "task" field is trusted; a "document" field (a maintenance ticket or manual excerpt) is untrusted content the agent must read as reference data only, never as an instruction.`),
        h2("2.2 Agent configurations under test"),
        bullet("Undefended baseline — scans the full combined context (task + document) for tool-call-shaped text and executes the first one found, modelling the failure mode described in Section 1.1/1.2: input treated as data can redirect the agent's plan."),
        bullet("AegisAI-style defended pipeline — runs the content detector on the untrusted document (Interception 1); block or hold verdicts stop the call before it reaches a tool; an allow verdict still only permits tool calls that appear in the trusted task field (Interception 3 / FR-6 baseline check), never in the document."),
        h2("2.3 Detector"),
        p("A pattern-weighted heuristic detector (src/detector.py) scores each document against 15 rules covering instruction-override phrasing, forged system/admin tags, delimiter-escape attempts, role-play framing, safety-bypass pretexts, fake tool-response instructions, base64-style blobs, policy-priming language, embedded tool-call syntax, and suspicious destination addresses. Scores below 2.0 allow, 2.0–3.99 hold for human review, 4.0+ block — mirroring the two-threshold decide/hold/block pipeline in Section 3.2."),

        h1("3. Attack Corpus (v" + corpus.corpus_version + ")"),
        p(`${corpus.samples.filter(s=>s.label==="attack").length} attack samples spanning 12 distinct text-injection techniques, plus ${corpus.samples.filter(s=>s.label==="benign").length} benign control samples designed to probe false positives (they reuse trigger words like "ignore," "system," and "setpoint" in harmless contexts). The full corpus is stored as versioned JSON (corpus/text_injection_corpus_v1.0.0.json) per NFR-6 (reproducibility) and FR-11 (versioned attack corpus).`),
        corpusTable,
        caption("Table 1. Attack corpus — 12 attack techniques and 6 benign controls."),

        h1("4. Test Procedure"),
        bullet("Each of the 18 corpus samples is run once against the undefended baseline and once against the defended pipeline (src/run_tests.py)."),
        bullet("For attack samples, 'attack success' = the unsafe/attacker-targeted tool call was actually executed."),
        bullet("For benign samples, 'false positive' = the defended pipeline held or blocked a document containing no real attack."),
        bullet("Decision latency is measured per call. Full raw output is written to results/results.json and results/results.csv for independent re-verification, satisfying NFR-6."),

        h1("5. Results"),
        metricsTable,
        caption("Table 2. Summary metrics from the test run."),
        new Paragraph({ text: "", spacing: { after: 200 } }),
        resultsTable,
        caption("Table 3. Per-sample outcome, undefended vs. defended."),

        ...(comparison ? [
          h1("6. AI Model Comparison"),
          p("The selected hosted, local, or open-source models received the same trusted task and untrusted document and were asked to identify whether the document contained a prompt injection. API or local-runtime errors are reported separately and are not counted as correct or incorrect classifications."),
          modelTable,
          caption("Table 4. Model-level classification comparison."),
          modelDetailTable,
          caption("Table 5. Per-sample model predictions. N/A indicates an API or response error."),
          p("Per-sample model decisions, confidence values, explanations, latency, and errors are stored in results/model_comparison.csv and results/model_comparison.json."),
        ] : []),

        h1(comparison ? "7. Discussion" : "6. Discussion"),
        p(`Under the undefended baseline, ${S.undefended.attack_success_rate_pct}% of the 12 attack samples executed their intended unsafe tool call — the agent could not tell an instruction embedded in untrusted data from a real operator instruction, exactly the failure mode Section 1.2 warns about. Under the AegisAI-style defended pipeline, attack success dropped to ${S.defended.attack_success_rate_pct}%, with ${S.defended.false_positive_rate_pct}% false positives on the benign controls.`),
        p("Two attack samples (TXT-04, payload splitting, and TXT-12, the trigger-word-free polite override) were not caught by the content detector itself — both reached an 'allow' verdict. They were still stopped because the defended pipeline only executes tool calls found in the trusted task field, never the document (Interception 3 / FR-6). This is worth reporting explicitly: it is evidence for the layered design chosen in Section 3.2 (client-side wrapper plus a small fixed policy layer), since detector-layer misses were caught by the baseline-enforcement layer rather than the detector never being wrong. A detector-only defense, without the baseline check, would have had a residual attack success rate of 2/12 (16.7%), not 0%."),
        p("Four attack samples (TXT-03, TXT-06, TXT-10, TXT-11) were held for human review rather than blocked outright, matching the intended handling of near-normal adversarial phrasing identified as a gap in Section 2.3 (Gap: GAN-based detection struggles on subtle attacks, no human fallback) rather than being silently passed."),

        h1(comparison ? "8. Limitations" : "7. Limitations"),
        bullet("This is a rule-based prototype, not the ML-based detector or the CrewAI/LangGraph agent that FYDP-2 will build (Table 3.4, P4–P6). Results characterize this specific ruleset and corpus, not the eventual system."),
        bullet("The agent simulator is deterministic and does not reason about intent the way an LLM-driven agent would; a real agent could be fooled by phrasing this ruleset happens to catch, or resist phrasing this ruleset happens to miss."),
        bullet("Static attacks only. Per FR-12 and the NAACL 2025 adaptive-attacks finding cited in Section 2.2.2, a defense-aware adaptive attacker with knowledge of these exact 15 rules could likely construct bypasses; that evaluation is scheduled for FYDP-3 (P9) against the real system."),
        bullet("The corpus covers only the text channel (12 techniques). Image-based and hybrid multimodal injection (FR-4, FR-5) require the image/hybrid detectors, which are FYDP-2 deliverables."),
        bullet("Latency figures (well under 1ms) are not representative of NFR-1's 300ms budget, since this ruleset has no model-inference cost; a real detector's latency must be measured separately once built."),

        h1(comparison ? "9. Reproducibility" : "8. Reproducibility"),
        p("Directory layout: corpus/text_injection_corpus_v1.0.0.json (versioned corpus), src/detector.py (heuristic detector), src/agent.py (undefended + defended agent simulators), src/run_tests.py (test runner). Run with: python3 src/run_tests.py from the project root. This regenerates results/results.json and results/results.csv from the corpus and code alone, with no external dependencies, satisfying NFR-6."),

        h1(comparison ? "10. Next Steps" : "9. Next Steps"),
        bullet("Fold this corpus into the versioned attack corpus being built for P5 (FYDP-2, weeks 3–7), extending it with adaptive variants for FYDP-3."),
        bullet("Replace the rule-based detector with the real text/hybrid detector once the CrewAI/LangGraph testbed (P4) exists, and re-run this exact procedure against it for a like-for-like comparison."),
        bullet("Add the review-queue UI (P7) so 'hold' verdicts route to an actual human reviewer rather than being counted as blocked for this prototype's ASR calculation."),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(__dirname + "/../results/AegisAI_Model_Comparison_Report.docx", buf);
  console.log("written");
});
