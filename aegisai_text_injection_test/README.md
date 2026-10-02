# AegisAI Text Injection Test

A reproducible test harness for evaluating text-based prompt-injection defenses and comparing AI models on the same corpus.

For the parallel multimodal workflow, see [image_injection_test](image_injection_test/README.md). It evaluates image-embedded injections, custom image sets, prompts, and vision-capable Ollama, Hugging Face, hosted, and local models without changing the text harness.

The project:

- Runs an undefended baseline agent and an AegisAI-style defended pipeline.
- Tests 18 versioned samples: attack cases and benign controls.
- Compares local Ollama models, OpenAI-compatible local servers, OpenAI, Anthropic, Gemini, and Hugging Face models.
- Records accuracy, attack detection, benign rejection, false positives, errors, confidence, explanations, and latency.
- Generates CSV, JSON, PPTX, DOCX, and an offline graphical HTML dashboard.

## Project Layout

```text
.
|-- corpus/
|   `-- text_injection_corpus_v1.0.0.json
|-- results/
|   |-- results.csv
|   |-- results.json
|   |-- model_comparison.csv
|   |-- model_comparison.json
|   |-- model_comparison_dashboard.html
|   |-- AegisAI_Model_Comparison_Report.pptx
|   `-- AegisAI_Model_Comparison_Report.docx
|-- src/
|   |-- agent.py
|   |-- detector.py
|   |-- model_eval.py
|   |-- run_tests.py
|   |-- select_model.py
|   |-- generate_model_dashboard.js
|   |-- generate_pptx.js
|   `-- generate_docx.js
|-- models.json
|-- MODEL_TESTING.md
`-- package.json
```

## Requirements

Install these before running the project:

- Windows PowerShell, macOS/Linux shell, or an equivalent terminal
- Python 3.10 or newer
- Node.js 18 or newer for DOCX and dashboard generation
- npm, installed with Node.js
- Ollama only if using `ollama:model`
- API keys only if using hosted providers

Check Python and Node:

```powershell
python --version
node --version
npm --version
```

## Setup From Scratch

Open PowerShell in the project root, the folder containing `src`, `models.json`, and `corpus`.

```powershell
cd "E:\path\to\aegisai_text_injection_test"
```

Install the Node dependency used by the DOCX generator:

```powershell
npm install
```

The Python evaluation scripts use only the standard library, so no `pip install` command is required.

### First-run setup

Use the project launcher for commands that need Node.js. It checks the local prerequisites and asks for permission before installing missing Node packages:

```text
python bootstrap.py --check
python bootstrap.py -- python src/run_tests.py
python bootstrap.py -- node src/generate_docx.js
```

On Windows, `run.cmd node src/generate_docx.js` or `run.ps1 node src/generate_docx.js` can be used. On macOS and Linux, use `./run.sh node src/generate_docx.js`. The same wrapper works for any command; Python itself must already be installed because it runs the checker.

The wrapper cannot intercept arbitrary commands typed directly into a shell. For consistent prerequisite checks after downloading the project, use the launcher or the npm scripts (`npm run generate:docx`, `npm run generate:pptx`, and `npm run generate:dashboard`).

Check the model catalog and current selection:

```powershell
python src\select_model.py list
```

## Run the Baseline and Detector

Run the deterministic baseline and defended pipeline without any AI model comparison:

```powershell
python src\run_tests.py
```

This writes:

- `results/results.json`
- `results/results.csv`

The baseline and defended results are based on the versioned corpus in `corpus/text_injection_corpus_v1.0.0.json`.

## Select Models

Models use this format:

```text
provider:model
```

Examples:

```text
ollama:qwen2.5:0.5b
openai:gpt-4o-mini
anthropic:claude-3-5-haiku-latest
gemini:gemini-2.0-flash
hf:google/gemma-2-2b-it
local:llama3
```

List the catalog. A `*` marks models currently selected in `models.json`:

```powershell
python src\select_model.py list
```

Select one catalog entry by its number:

```powershell
python src\select_model.py select 1
```

Select multiple catalog entries:

```powershell
python src\select_model.py select 1,2,3
```

Add a custom model ID to the saved selection:

```powershell
python src\select_model.py add ollama:my-custom-model
```

Remove a saved model:

```powershell
python src\select_model.py remove ollama:my-custom-model
```

The saved selection is stored in `models.json` under `selected_models`.

## Run One Model

Run one model for all 18 corpus samples:

```powershell
python src\run_tests.py --models "ollama:qwen2.5:0.5b"
```

Set a longer per-request timeout when using a slower model:

```powershell
python src\run_tests.py --models "ollama:qwen2.5:1.5b" --timeout 120
```

The `--models` option overrides the selection in `models.json` for that run only.

## Run Multiple Models

Compare several local models:

```powershell
python src\run_tests.py --models "ollama:qwen2.5:0.5b,ollama:qwen2.5:1.5b,ollama:llama3.2:1b" --timeout 120
```

Compare different providers:

```powershell
python src\run_tests.py --models "ollama:qwen2.5:1.5b,openai:gpt-4o-mini,gemini:gemini-2.0-flash"
```

Run the models saved in `models.json`:

```powershell
python src\run_tests.py --timeout 120
```

For unattended runs, automatically download missing selected Ollama models:

```powershell
python src\run_tests.py --yes-download --timeout 120
```

Before testing, the runner lists installed Ollama models. If a selected Ollama model is missing, it displays the exact download command and asks:

```text
Download the missing model(s) now? [y/N]:
```

Answer `y` or `yes` to download. Any other answer cancels the evaluation before the tests start.

## Ollama Models

Install Ollama from [ollama.com](https://ollama.com), start the Ollama application, and check installed models:

```powershell
ollama list
python src\select_model.py ollama
```

Download individual models:

```powershell
ollama pull qwen2.5:0.5b
ollama pull qwen2.5:1.5b
ollama pull llama3.2:1b
```

Run a downloaded model:

```powershell
python src\run_tests.py --models "ollama:qwen2.5:0.5b"
```

The default Ollama server is:

```text
http://localhost:11434
```

Use a different Ollama server address in PowerShell:

```powershell
$env:OLLAMA_URL="http://localhost:11434"
```

The model name must exactly match the name shown by `ollama list`. A missing model normally produces HTTP 404 errors; the built-in preflight now detects this before evaluation.

## Hosted API Keys

API keys are read from environment variables. Do not put secrets in `models.json`, source files, CSV files, or this README.

### OpenAI

PowerShell for the current terminal session:

```powershell
$env:OPENAI_API_KEY="your-openai-api-key"
python src\run_tests.py --models "openai:gpt-4o-mini"
```

### Anthropic

```powershell
$env:ANTHROPIC_API_KEY="your-anthropic-api-key"
python src\run_tests.py --models "anthropic:claude-3-5-haiku-latest"
```

### Google Gemini

```powershell
$env:GOOGLE_API_KEY="your-google-api-key"
python src\run_tests.py --models "gemini:gemini-2.0-flash"
```

### Hugging Face

Anonymous inference is attempted first. Set a token for gated, rate-limited, or private models:

```powershell
$env:HF_TOKEN="hf_your-token"
python src\run_tests.py --models "hf:google/gemma-2-2b-it"
```

Hugging Face models may be cold, gated, rate-limited, or unavailable. These failures are recorded in the model comparison results.

## OpenAI-Compatible Local Server

Any server exposing `/v1/chat/completions` can be used with `local:model`.

The default server address is:

```text
http://localhost:8000
```

Configure another address:

```powershell
$env:LOCAL_LLM_URL="http://localhost:8000"
python src\run_tests.py --models "local:llama3"
```

The local server must accept a payload containing `model`, `temperature`, and `messages` and return an OpenAI-compatible response with:

```json
{
  "choices": [
    {
      "message": {
        "content": "{\"attack\": false, \"confidence\": 0.9, \"reason\": \"...\"}"
      }
    }
  ]
}
```

## Generate Reports

After running a model evaluation, generate the PowerPoint report:

```powershell
node src\generate_pptx.js
```

The PowerPoint contains overview, quality, speed/reliability, attack-technique, and dynamically paginated per-sample detail slides for every selected model. Detail slides include category, prediction, correctness, confidence, latency, reason, and errors.

The older DOCX report can still be generated separately if needed:

```powershell
node src\generate_docx.js
```

Generate the offline graphical dashboard:

```powershell
node src\generate_model_dashboard.js
```

The dashboard can be opened directly in a browser:

```text
results/model_comparison_dashboard.html
```

The dashboard includes two export buttons:

- **Download PowerPoint** downloads `AegisAI_Model_Comparison_Report.pptx` generated by `src/generate_pptx.js`.
- **Generate PDF** opens the browser print dialog. Select **Save as PDF** as the printer or destination.

The PDF print layout hides the dashboard buttons and uses print-friendly page styling.

It does not require an internet connection. It includes:

- Accuracy, attack detection, benign correctness, and false-positive charts
- Successful calls versus errors
- Average latency
- Prediction mix pie/donut chart
- Correct versus incorrect decisions
- Average confidence
- Attack-technique heatmap
- Detailed per-sample comparison

The detailed dashboard table assigns a different color to each model group and inserts a gap whenever the model changes. Colors and gaps are generated dynamically from the model list.

## Output Files

### `results/results.json`

Machine-readable baseline and defended-pipeline summary plus per-sample rows.

### `results/results.csv`

Spreadsheet-friendly baseline and defended-pipeline results.

### `results/model_comparison.json`

Model summaries and detailed per-sample AI predictions.

### `results/model_comparison.csv`

Per-sample model predictions with:

- Model name
- Corpus sample ID and label
- Predicted attack value
- Correctness
- Confidence
- Model reason
- Error text
- Latency

When the model changes, the exporter inserts two rows containing blank cells across every CSV column. This makes model ranges easy to identify in spreadsheet applications and updates automatically when models are added, removed, or reordered.

### `results/model_comparison_dashboard.html`

Offline graphical comparison dashboard generated from `model_comparison.json`.

### `results/AegisAI_Model_Comparison_Report.pptx`

PowerPoint report containing overview, model quality, latency/reliability, and attack-technique comparison slides.

### `results/AegisAI_Model_Comparison_Report.docx`

Optional legacy Word report generated by `src/generate_docx.js`.

## Understanding the Metrics

- **Accuracy:** Correct predictions across valid model calls.
- **Attack detection rate:** Percentage of attack samples predicted as attacks.
- **Benign correctly rejected:** Percentage of benign samples predicted as not attacks.
- **False-positive rate:** Percentage of benign samples incorrectly predicted as attacks.
- **Successful calls:** Model calls that returned parseable classification JSON.
- **Errors:** Calls that failed because of an unavailable model, timeout, API error, or invalid response.
- **Confidence:** The model-reported value from 0 to 1.
- **Average latency:** Average time for one model request in milliseconds.

Errors are not counted as correct or incorrect classifications. If every call for a model fails, its percentage metrics appear as `N/A` or `None` rather than being treated as detections.

## Expected Model Response

Each model must return JSON containing these keys:

```json
{
  "attack": true,
  "confidence": 0.95,
  "reason": "The document contains an instruction that attempts to control the AI."
}
```

The evaluator accepts a JSON object embedded in surrounding text, but the safest response format is JSON only. `attack` must be a boolean, and `confidence` should be between 0 and 1.

## Troubleshooting

### `ollama:...` returns HTTP 404

Check the exact installed tag:

```powershell
ollama list
```

Download the missing tag:

```powershell
ollama pull qwen2.5:1.5b
```

Then rerun the test. Do not replace a tag such as `qwen2.5:1.5b` with `qwen2.5` unless that exact tag is installed.

### Ollama is not available

Confirm that Ollama is installed and running:

```powershell
Get-Command ollama
ollama list
```

If the command is not found, install Ollama and restart PowerShell so its executable is on `PATH`.

### Hosted provider says an API key is missing

Set the matching variable in the same terminal where the test is run:

```powershell
$env:OPENAI_API_KEY="..."
$env:ANTHROPIC_API_KEY="..."
$env:GOOGLE_API_KEY="..."
```

Environment variables set with `$env:` apply to the current PowerShell session. They are not written permanently by this project.

### A model has many errors

Inspect the detailed error column:

```powershell
Get-Content results\model_comparison.csv
```

Common causes include a wrong model tag, stopped local server, missing API key, request timeout, rate limit, gated endpoint, or a response that is not valid JSON.

Increase the timeout for slow local models:

```powershell
python src\run_tests.py --models "ollama:your-model" --timeout 180
```

### The percentages are `None` or `N/A`

This means there were no valid classifications for that model. Check the `error` field in `model_comparison.csv` or `model_comparison.json`.

### The DOCX generator fails

Install Node dependencies from the project root:

```powershell
npm install
```

Then retry:

```powershell
node src\generate_docx.js
```

### The dashboard looks unchanged

Regenerate it after running tests:

```powershell
node src\generate_model_dashboard.js
```

Then reopen `results/model_comparison_dashboard.html` or refresh the browser.

## Reproducibility Workflow

A typical complete run is:

```powershell
npm install
python src\select_model.py list
ollama list
python src\run_tests.py --models "ollama:qwen2.5:0.5b,ollama:qwen2.5:1.5b,ollama:llama3.2:1b" --timeout 120
node src\generate_model_dashboard.js
node src\generate_docx.js
```

For hosted models, set the required API key before the `run_tests.py` command.

## Security Notes

- Keep API keys in environment variables and never commit them.
- The document field in the corpus is treated as untrusted input.
- The trusted task and untrusted document are sent to the model with explicit instructions to classify only the document.
- This is a prototype evaluation harness, not a production security boundary.
- Results depend on the corpus, model version, model settings, provider availability, and local hardware.

## More Documentation

- [MODEL_TESTING.md](MODEL_TESTING.md): focused model-testing instructions
- [models.json](models.json): model catalog and saved selection
- [corpus/text_injection_corpus_v1.0.0.json](corpus/text_injection_corpus_v1.0.0.json): versioned test corpus
