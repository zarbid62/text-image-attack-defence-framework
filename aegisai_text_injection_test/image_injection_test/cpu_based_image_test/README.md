# CPU-Based Image Test

This folder contains the low-memory workflow for image prompt-injection testing with Ollama. It is designed for CPU-only machines and avoids large test batches.

## Recommended profiles

| Profile | Recommended model | Safe default samples | Timeout | Use case |
|---|---|---:|---:|---|
| `8gb` | `ollama:moondream` | 1 | 300 seconds | Safest option for an 8 GB computer without a GPU |
| `16gb` | `ollama:qwen2.5vl:3b` | 2 | 300 seconds | Better capability with a small CPU workload |
| `more` | `ollama:llava` | 4 | 600 seconds | Larger CPU test; monitor memory and expect slow inference |

The profile controls the recommended model, default sample limit, and timeout. It does not download a model automatically unless `--yes-download` is supplied.

## Setup

Run these commands from the `image_injection_test` directory:

```powershell
ollama --version
ollama list
ollama pull moondream
```

For an 8 GB machine, do not start with `llava`, `minicpm-v`, or 7B/12B vision models.

## Small defended test

```powershell
python src\run_tests.py `
  --cpu-only `
  --cpu-profile 8gb `
  --attack-prompt-id direct_override `
  --overlay-attack-prompt `
  --defense-mode defense `
  --defense-prompt-id layered_defense
```

The profile supplies `ollama:moondream`, one sample, CPU-only mode, and a 300-second timeout.

## Test all attack types safely

This runs one image per attack type. It is still sequential and CPU-only, but eight model requests can take several minutes:

```powershell
python src\run_tests.py `
  --cpu-only `
  --cpu-profile 8gb `
  --models "ollama:moondream" `
  --attack-prompt-id direct_override `
  --overlay-attack-prompt `
  --defense-mode defense `
  --defense-prompt-id layered_defense
```

For the full attack catalog, run the same command once for each attack ID listed in `COMMANDS.md`.

## Reports and preserved history

Every model run records the command, run ID, attack ID/type, complete injected prompt, defense ID/type/prompt, image, prediction, confidence, latency, and errors.

Before a new run writes the latest result files, the previous results and reports are copied to:

```text
results\history\<run-id>\
```

Generated reports include:

- `results\LAYERED_DEFENSE_ATTACK_CATALOG.md`
- `results\IMAGE_TEST_RUN_REPORT.md`
- `results\image_model_comparison_dashboard.html`
- `results\attack_defense_report.html`
- DOCX, PDF, and PPTX reports

## Troubleshooting

- If a model is missing, run `ollama pull <model>` or add `--yes-download`.
- If memory is tight, use `--cpu-profile 8gb --max-samples 1`.
- If inference is slow, keep one model, one image, and a timeout of at least 300 seconds.
- If an image request fails, confirm that the selected model is vision-capable.
- The CPU profile does not make Ollama faster; it prevents oversized test choices.
