# Model Testing

The test runner supports hosted, free/open-source, and local models. Every model receives the same 18 corpus samples and must return JSON containing `attack`, `confidence`, and `reason`.

## Select models with the model manager

The available catalog and current selection are stored in `models.json`. List the catalog:

```powershell
python src\select_model.py list
```

Select one model:

```powershell
python src\select_model.py select 1
```

Select several models at the same time:

```powershell
python src\select_model.py select 1,2,3,9,10,11,12,13
```

Add a custom model ID and remove it later:

```powershell
python src\select_model.py add ollama:my-custom-model
python src\select_model.py remove ollama:my-custom-model
```

The runner automatically uses `selected_models` from `models.json`:

```powershell
python src\run_tests.py --timeout 120
node src\generate_pptx.js
```

Before testing, the runner lists installed Ollama models. If one or more selected Ollama models are missing, it shows the exact `ollama pull ...` command for each and asks whether to download them. Answer `y` to download, or use `--yes-download` for an unattended run:

```powershell
python src\run_tests.py --yes-download
```

Use `--models` when a one-time command-line selection is preferable; it overrides the JSON selection:

```powershell
python src\run_tests.py --models "ollama:qwen2.5:0.5b,ollama:llama3.2:1b,openai:gpt-4o-mini"
```

To see models installed in Ollama:

```powershell
python src\select_model.py ollama
```

## Local Ollama: no API key

Install Ollama, start it, download a model, and run the evaluation:

```powershell
ollama pull llama3.2
python src\run_tests.py --models "ollama:llama3.2"
node src\generate_docx.js
```

The default Ollama address is `http://localhost:11434`. Use another address with:

```powershell
$env:OLLAMA_URL="http://localhost:11434"
```

## Other local LLM servers: no API key

Any OpenAI-compatible local server can be used with `local:model`. The default address is `http://localhost:8000`:

```powershell
$env:LOCAL_LLM_URL="http://localhost:8000"
python src\run_tests.py --models "local:llama3"
```

## Hugging Face open-source endpoint

The `hf:model` option attempts anonymous inference first. Some models or current Hugging Face infrastructure require a free Hugging Face token:

```powershell
$env:HF_TOKEN="hf_your_token"
python src\run_tests.py --models "hf:google/gemma-2-2b-it"
```

This is not guaranteed to be unlimited or permanently free. A model endpoint can be unavailable, cold, rate-limited, or gated; those cases are recorded as errors in `results/model_comparison.csv`.

## Compare several backends

```powershell
python src\run_tests.py --models "ollama:llama3.2,hf:google/gemma-2-2b-it,openai:gpt-4o-mini"
node src\generate_docx.js
```

Outputs:

- `results/model_comparison.csv`: detailed per-sample predictions, confidence, reason, latency, and errors.
- `results/model_comparison.json`: machine-readable summary and detailed rows.
- `results/model_comparison_dashboard.html`: offline graphical dashboard with bar charts, a prediction pie chart, latency and error comparisons, an attack-technique heatmap, and a detailed comparison table.
- `results/AegisAI_Model_Comparison_Report.pptx`: PowerPoint comparison report with overview, quality, speed/reliability, and attack-technique slides.

Generate the graphical dashboard after a model evaluation:

```powershell
node src\generate_model_dashboard.js
```

Open `results/model_comparison_dashboard.html` in a browser. It uses the saved JSON results and does not need an internet connection or another package.

Model sections in the CSV and dashboard detail table are separated automatically whenever the model name changes. The separator is based on the actual model value, not fixed row numbers, so it remains correct when models are added, removed, or reordered.

Missing keys, unavailable models, and invalid responses are shown as `N/A` metrics and errors. They are never treated as attack detections or successful benign classifications.