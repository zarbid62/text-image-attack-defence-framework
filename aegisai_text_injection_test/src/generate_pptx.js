const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const root = path.join(__dirname, "..");
const comparisonPath = path.join(root, "results", "model_comparison.json");
const baselinePath = path.join(root, "results", "results.json");
const outputPath = path.join(root, "results", "AegisAI_Model_Comparison_Report.pptx");

if (!fs.existsSync(comparisonPath)) {
  console.error("Missing results/model_comparison.json. Run src\\run_tests.py first.");
  process.exit(1);
}

const comparison = JSON.parse(fs.readFileSync(comparisonPath, "utf8"));
const baseline = fs.existsSync(baselinePath) ? JSON.parse(fs.readFileSync(baselinePath, "utf8")) : null;
const models = comparison.models;
const rows = comparison.rows;
const colors = { ink: "17212B", muted: "64717D", teal: "087F8C", blue: "3B67C4", green: "2F9560", amber: "D58B18", coral: "D85D50", line: "DCE3E7", pale: "F5F7F8" };
const modelColors = ["E6F4F1", "E8EEFB", "FFF1D9", "F5E8F2", "E9F1DF", "FBE6E2", "E7EDF0"];

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "AegisAI Text Injection Test";
pptx.subject = "AI model comparison";
pptx.title = "AegisAI Model Comparison Report";
pptx.company = "AegisAI";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "en-US",
};
pptx.defineSlideMaster({
  title: "MASTER",
  background: { color: "F5F7F8" },
  objects: [
    { line: { x: 0.45, y: 7.1, w: 12.4, h: 0, line: { color: colors.line, width: 1 } } },
  ],
  slideNumber: { x: 12.35, y: 7.12, color: colors.muted, fontFace: "Aptos", fontSize: 8 },
});

function shortName(name) {
  return name.replace(/^ollama:/, "");
}

function addTitle(slide, title, subtitle) {
  slide.addText(title, { x: 0.55, y: 0.35, w: 8.8, h: 0.45, fontFace: "Aptos Display", fontSize: 25, bold: true, color: colors.ink, margin: 0 });
  if (subtitle) slide.addText(subtitle, { x: 0.58, y: 0.86, w: 11.8, h: 0.3, fontSize: 10.5, color: colors.muted, margin: 0 });
}

function metricCard(slide, x, y, w, label, value, detail, fill) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 1.08, rectRadius: 0.06, fill: { color: fill }, line: { color: fill } });
  slide.addText(label, { x: x + 0.16, y: y + 0.12, w: w - 0.32, h: 0.2, fontSize: 9, color: colors.muted, margin: 0 });
  slide.addText(value, { x: x + 0.16, y: y + 0.36, w: w - 0.32, h: 0.34, fontSize: 21, bold: true, color: colors.ink, margin: 0 });
  slide.addText(detail, { x: x + 0.16, y: y + 0.79, w: w - 0.32, h: 0.16, fontSize: 8, color: colors.muted, margin: 0, fit: "shrink" });
}

function percent(value) {
  return value == null ? "N/A" : `${value}%`;
}

const bestAccuracy = models.filter((m) => m.accuracy_pct != null).sort((a, b) => b.accuracy_pct - a.accuracy_pct)[0];
const bestDetection = models.filter((m) => m.attack_detection_rate_pct != null).sort((a, b) => b.attack_detection_rate_pct - a.attack_detection_rate_pct)[0];
const fastest = models.filter((m) => m.avg_latency_ms != null).sort((a, b) => a.avg_latency_ms - b.avg_latency_ms)[0];

// Slide 1: overview.
{
  const slide = pptx.addSlide("MASTER");
  addTitle(slide, "AegisAI model comparison", "Performance summary from the current text-injection evaluation");
  metricCard(slide, 0.6, 1.45, 2.85, "Best accuracy", bestAccuracy ? percent(bestAccuracy.accuracy_pct) : "N/A", bestAccuracy ? shortName(bestAccuracy.model) : "No valid result", "E6F4F1");
  metricCard(slide, 3.65, 1.45, 2.85, "Best attack detection", bestDetection ? percent(bestDetection.attack_detection_rate_pct) : "N/A", bestDetection ? shortName(bestDetection.model) : "No valid result", "E8EEFB");
  metricCard(slide, 6.7, 1.45, 2.85, "Fastest average", fastest ? `${Math.round(fastest.avg_latency_ms)} ms` : "N/A", fastest ? shortName(fastest.model) : "No valid result", "FFF1D9");
  metricCard(slide, 9.75, 1.45, 2.85, "Models evaluated", String(models.length), `${rows.length} total model samples`, "F5E8F2");

  slide.addText("What this report shows", { x: 0.65, y: 3.05, w: 4, h: 0.3, fontSize: 17, bold: true, color: colors.ink, margin: 0 });
  slide.addText([
    { text: "• Same 18 corpus samples sent to every selected model\n" },
    { text: "• Attack detection, benign handling, accuracy, confidence, errors, and latency\n" },
    { text: "• Errors are reported separately and are not counted as correct predictions\n" },
    { text: "• Results are generated from results/model_comparison.json" },
  ], { x: 0.72, y: 3.48, w: 5.9, h: 1.6, fontSize: 15, breakLine: false, color: colors.ink, margin: 0.04, valign: "mid" });

  if (baseline && baseline.summary) {
    slide.addText("Defended pipeline context", { x: 7.0, y: 3.05, w: 4.5, h: 0.3, fontSize: 17, bold: true, color: colors.ink, margin: 0 });
    slide.addText(`Attack success rate: ${baseline.summary.defended.attack_success_rate_pct}%\nFalse-positive rate: ${baseline.summary.defended.false_positive_rate_pct}%\nAttacks blocked: ${baseline.summary.defended.attacks_blocked}\nHeld for review: ${baseline.summary.defended.attacks_held_for_review}`, { x: 7.08, y: 3.5, w: 4.8, h: 1.4, fontSize: 15, color: colors.ink, breakLine: false, margin: 0.04 });
  }
}

// Slide 2: model metric table and quality chart.
{
  const slide = pptx.addSlide("MASTER");
  addTitle(slide, "Model quality comparison", "Higher is better for accuracy, attack detection, and benign correctness");
  const tableRows = [
    ["Model", "Accuracy", "Attack detection", "Benign correct", "False positives", "Errors"],
    ...models.map((m) => [shortName(m.model), percent(m.accuracy_pct), percent(m.attack_detection_rate_pct), percent(m.benign_correctly_rejected_as_not_attack_pct), percent(m.false_positive_rate_pct), String(m.errors)]),
  ];
  slide.addTable(tableRows, {
    x: 0.55, y: 1.3, w: 6.15, h: 2.4,
    border: { type: "solid", color: colors.line, pt: 1 },
    fill: "FFFFFF", color: colors.ink, fontFace: "Aptos", fontSize: 10,
    margin: 0.08, rowH: 0.34,
    bold: false,
    autoFit: false,
    colW: [1.65, 0.83, 1.15, 1.15, 1.05, 0.55],
    fill: "FFFFFF",
  });
  slide.addChart(pptx.ChartType.bar, [
    { name: "Accuracy", labels: models.map((m) => shortName(m.model)), values: models.map((m) => m.accuracy_pct || 0) },
    { name: "Attack detection", labels: models.map((m) => shortName(m.model)), values: models.map((m) => m.attack_detection_rate_pct || 0) },
    { name: "Benign correct", labels: models.map((m) => shortName(m.model)), values: models.map((m) => m.benign_correctly_rejected_as_not_attack_pct || 0) },
  ], {
    x: 6.95, y: 1.2, w: 5.75, h: 4.6,
    catAxisLabelFontSize: 10, valAxisLabelFontSize: 9, showLegend: true, legendFontSize: 9,
    showTitle: false, showValue: true, valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 20,
    chartColors: [colors.teal, colors.blue, colors.green], showCatName: false,
    showGridLines: true, gridLine: { color: colors.line, pt: 1 },
  });
  slide.addText("N/A means the model had no valid classifications for that metric.", { x: 0.62, y: 4.05, w: 5.8, h: 0.25, fontSize: 10, italic: true, color: colors.muted, margin: 0 });
}

// Slide 3: latency and reliability.
{
  const slide = pptx.addSlide("MASTER");
  addTitle(slide, "Speed and reliability", "Latency is measured per model request; errors are separate from valid predictions");
  slide.addChart(pptx.ChartType.bar, [{ name: "Average latency (ms)", labels: models.map((m) => shortName(m.model)), values: models.map((m) => Math.round(m.avg_latency_ms || 0)) }], {
    x: 0.55, y: 1.25, w: 6.1, h: 4.9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 9,
    showLegend: false, showValue: true, chartColors: [colors.amber], showTitle: true, title: "Average latency (lower is faster)", titleFontSize: 14,
    showGridLines: true, gridLine: { color: colors.line, pt: 1 },
  });
  slide.addChart(pptx.ChartType.bar, [
    { name: "Successful calls", labels: models.map((m) => shortName(m.model)), values: models.map((m) => m.successful_calls || 0) },
    { name: "Errors", labels: models.map((m) => shortName(m.model)), values: models.map((m) => m.errors || 0) },
  ], {
    x: 6.9, y: 1.25, w: 5.8, h: 4.9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 9,
    showLegend: true, legendFontSize: 9, showValue: true, chartColors: [colors.green, colors.coral],
    showTitle: true, title: "Successful calls versus errors", titleFontSize: 14,
    showGridLines: true, gridLine: { color: colors.line, pt: 1 },
  });
}

// Slide 4: attack technique heatmap-style table.
{
  const slide = pptx.addSlide("MASTER");
  addTitle(slide, "Attack detection by technique", "Percentage of attack samples in each technique classified as attacks");
  const attacks = rows.filter((r) => r.label === "attack");
  const categories = [...new Set(attacks.map((r) => r.category))];
  const table = [["Attack technique", ...models.map((m) => shortName(m.model))]];
  categories.forEach((category) => {
    const samples = attacks.filter((r) => r.category === category);
    table.push([category, ...models.map((m) => {
      const relevant = samples.filter((r) => r.model === m.model);
      if (!relevant.length) return "N/A";
      return `${Math.round(relevant.filter((r) => r.predicted_attack === true).length / relevant.length * 100)}%`;
    })]);
  });
  slide.addTable(table, {
    x: 0.45, y: 1.25, w: 12.35, h: 5.5, border: { type: "solid", color: colors.line, pt: 1 },
    fill: "FFFFFF", color: colors.ink, fontSize: 10, margin: 0.07, rowH: 0.33,
    colW: [3.15, ...models.map(() => Math.max(1.0, 9.2 / Math.max(models.length, 1)))],
    bold: false,
  });
  slide.addText("Darker results indicate stronger detection. This view is generated dynamically for the selected models.", { x: 0.55, y: 6.8, w: 11.5, h: 0.22, fontSize: 9, italic: true, color: colors.muted, margin: 0 });
}

// Detailed per-sample slides: every model row is included, split into readable pages.
const detailRowsPerSlide = 9;
const detailColumns = ["ID", "Label", "Category", "Predicted", "Correct", "Confidence", "Latency", "Reason / error"];
const detailWidths = [0.55, 0.65, 1.85, 0.78, 0.65, 0.8, 0.75, 6.35];
models.forEach((model) => {
  const modelRows = rows.filter((row) => row.model === model.model);
  for (let start = 0; start < modelRows.length; start += detailRowsPerSlide) {
    const slide = pptx.addSlide("MASTER");
    const pageRows = modelRows.slice(start, start + detailRowsPerSlide);
    addTitle(slide, `${shortName(model.model)} — detailed results`, `Samples ${start + 1}-${start + pageRows.length} of ${modelRows.length}`);
    const tableRows = [detailColumns, ...pageRows.map((row) => [
      row.id,
      row.label,
      row.category,
      row.predicted_attack === null ? "N/A" : (row.predicted_attack ? "attack" : "benign"),
      row.correct === null ? "N/A" : (row.correct ? "yes" : "no"),
      row.confidence === null ? "N/A" : String(row.confidence),
      `${Math.round(row.latency_ms || 0)} ms`,
      row.error || row.reason || "No explanation returned",
    ])];
    slide.addTable(tableRows, {
      x: 0.35, y: 1.25, w: 12.55, h: 5.55,
      colW: detailWidths, rowH: 0.57,
      border: { type: "solid", color: colors.line, pt: 1 },
      fill: modelColors[models.indexOf(model) % modelColors.length],
      color: colors.ink, fontFace: "Aptos", fontSize: 8.5, margin: 0.06,
      valign: "mid", autoFit: false,
    });
    slide.addText("Errors are shown in the final column and are not counted as valid classifications.", { x: 0.45, y: 6.85, w: 8.5, h: 0.2, fontSize: 8.5, italic: true, color: colors.muted, margin: 0 });
  }
});

pptx.writeFile({ fileName: outputPath }).then(() => {
  console.log(`written ${outputPath}`);
}).catch((error) => {
  console.error(error);
  process.exit(1);
});
