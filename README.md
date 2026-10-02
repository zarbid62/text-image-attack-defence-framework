# AegisAI Text and Image Prompt-Injection Defense Framework

> A reproducible security evaluation framework for testing how AI systems distinguish trusted instructions from untrusted content embedded in text, images, and other data sources.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Research prototype](https://img.shields.io/badge/status-research%20prototype-087F8C)](#scope-and-responsible-use)

This project studies **prompt injection**, an attack in which untrusted content attempts to change an AI system's instructions, trigger tools, impersonate authority, bypass safety checks, or exfiltrate information. It provides repeatable corpora, deterministic baselines, transparent defenses, model comparisons, image overlays, and offline reports so that security claims can be inspected rather than inferred from a single demo.

It is designed as both:

- A practical lab for experimenting with text and multimodal AI safety controls.
- A portfolio-quality research artifact demonstrating Python, JavaScript, data modeling, evaluation design, reproducibility, and security reasoning.

## Why This Project Matters

Modern AI systems do not receive only clean user text. They also process documents, OCR transcripts, screenshots, diagrams, tool responses, web content, and other data that may contain instructions. The central engineering question is:

> Can an AI system distinguish trusted task instructions from untrusted content that merely looks authoritative?

This framework makes that question measurable across:

- Direct overrides and role reassignment.
- Forged authority and delimiter escapes.
- Role-play jailbreaks and urgency-based bypasses.
- Fake tool responses and embedded tool calls.
- Data-exfiltration requests.
- Polite, low-signal instruction attacks.
- Benign operational text such as notices, schedules, labels, and procedures.

## What It Demonstrates

### Security engineering

- Separates trusted review prompts from untrusted corpus or image text.
- Uses a transparent detector with scored categories and block/hold/allow decisions.
- Compares an undefended agent with a defended agent on identical inputs.
- Tests both OCR/transcript channels and actual image bytes.
- Preserves bypasses and errors as findings instead of hiding them.

### Evaluation engineering

- Uses versioned JSON corpora with attack and benign controls.
- Supports single-model runs, cross-provider comparisons, custom prompts, custom image sets, and HTTP manifests.
- Records accuracy, attack detection, attack bypass, false positives, errors, confidence, latency, prompts, model responses, and run IDs.
- Archives previous outputs under `results/history/<run-id>` before writing new results.

### Software engineering

- Provides Windows and Unix launchers for clone-and-run setup.
- Automatically installs missing Python image packages and Node report dependencies.
- Automatically downloads selected missing Ollama models, with `--no-download` for offline runs.
- Generates machine-readable JSON/CSV and human-readable Markdown, HTML, DOCX, PDF, and PowerPoint reports.

## Architecture

```mermaid
flowchart LR
	A[Attack corpus or custom image set] --> B[Runner]
	P[Trusted review prompt] --> B
	L[Attack and defense prompt library] --> B
	B --> C[Untrusted content loader]
	C --> D[Deterministic baseline]
	C --> E[Transparent detector]
	C --> F[Model provider adapters]
	P --> D
	P --> E
	P --> F
	D --> G[Comparison records]
	E --> G
	F --> G
	G --> H[JSON and CSV]
	G --> I[HTML dashboards]
	G --> J[DOCX, PDF, PPTX, Markdown]
```

### Core execution path

1. `bootstrap.py` checks Python, installs missing declared dependencies, and prepares Node dependencies when a Node command is requested.
2. `run_tests.py` loads a versioned corpus or custom image manifest.
3. `agent.py` runs a deterministic undefended and defended simulation.
4. `detector.py` scores instruction-like patterns such as role tags, overrides, urgency, tool calls, and exfiltration requests.
5. `model_eval.py` routes evaluations to Ollama, OpenAI-compatible local servers, OpenAI, Anthropic, Gemini, or Hugging Face providers.
6. The runner compares predictions with expected labels and writes reproducible results.
7. JavaScript report generators transform the results into offline dashboards and shareable documents.

## Repository Layout

```text
.
|-- run.cmd                         Windows clone-and-run launcher
|-- run.sh                          macOS/Linux clone-and-run launcher
|-- README.md                       This project overview
`-- aegisai_text_injection_test/
	|-- bootstrap.py                Dependency and prerequisite bootstrapper
	|-- corpus/                     Versioned text-injection corpus
	|-- src/                        Text evaluation and report tools
	|-- results/                    Text comparison outputs
	|-- image_injection_test/
	|   |-- corpus/                 Versioned image-injection corpus and assets
	|   |-- src/                    Image loading, detection, models, and reports
	|   |-- results/                Image dashboards and attack catalogs
	|   |-- models.json              Image model catalog
	|   |-- prompts.json             Attack and defense prompt library
	|   `-- requirements.txt         Python image-processing dependencies
	|-- models.json                  Text model catalog and saved selections
	|-- package.json                 JavaScript report dependencies
	`-- MODEL_TESTING.md             Model configuration and comparison guide
```

## Quick Start

### 1. Clone and check the project

```powershell
git clone https://github.com/zarbid62/text-image-attack-defence-framework.git
cd text-image-attack-defence-framework
.\run.cmd --check
```

On macOS or Linux:

```bash
git clone https://github.com/zarbid62/text-image-attack-defence-framework.git
cd text-image-attack-defence-framework
./run.sh --check
```

The launcher installs missing Python and Node dependencies when needed. Python 3.10+ is required. Node.js 18+ is needed for document and dashboard generation. Ollama is optional unless a local Ollama model is selected.

### 2. Run the deterministic text evaluation

```powershell
.\run.cmd python src\run_tests.py
```

This does not require an AI provider. It validates the corpus, baseline agent, detector, and result-writing path.

### 3. Run a CPU-based image test

```powershell
.\run.cmd python image_injection_test\src\run_tests.py
```

The CPU workflow is the recommended first experiment because it is affordable, reproducible, and suitable for laptops or lab computers without a GPU. It uses Ollama locally, keeps the sample count small, runs requests sequentially, and records enough metadata to support a research discussion.

#### CPU profiles

| Profile | Default model | Samples | Timeout | Best fit |
| --- | --- | ---: | ---: | --- |
| `8gb` | `ollama:moondream` | 1 | 300 seconds | Safest starting point for an 8 GB machine |
| `16gb` | `ollama:qwen2.5vl:3b` | 2 | 300 seconds | More capable evaluation with a small workload |
| `more` | `ollama:llava` | 4 | 600 seconds | Larger CPU experiment with careful memory monitoring |

The profile is a resource-management policy, not a performance claim. It selects a practical model, limits the number of samples, disables GPU selection, and increases the timeout for CPU inference. Missing selected models are downloaded automatically; use `--no-download` when working offline.

#### Recommended 8 GB experiment

```powershell
.\run.cmd python image_injection_test\src\run_tests.py `
	--cpu-only `
	--cpu-profile 8gb `
	--attack-prompt-id direct_override `
	--overlay-attack-prompt `
	--defense-mode defense `
	--defense-prompt-id layered_defense
```

This experiment creates a controlled attack image, sends it through the undefended and defended paths, evaluates the `moondream` vision model, and records the prediction, confidence, latency, prompt configuration, and image errors.

#### Compare without and with defense

```powershell
.\run.cmd python image_injection_test\src\run_tests.py `
	--cpu-only `
	--cpu-profile 8gb `
	--defense-mode both `
	--defense-prompt-id layered_defense `
	--timeout 300
```

This creates a useful paired experiment: the same inputs and model are evaluated without the defense prompt and with the defense prompt. The comparison helps answer whether the defense changes attack detection, bypass rate, false positives, errors, or latency.

#### Test all predefined attack types

```powershell
.\run.cmd python image_injection_test\src\run_tests.py `
	--cpu-only `
	--cpu-profile 8gb `
	--models "ollama:moondream" `
	--attack-prompt-id direct_override `
	--overlay-attack-prompt `
	--defense-mode defense `
	--defense-prompt-id layered_defense `
	--timeout 300
```

Repeat the command with the attack IDs in [COMMANDS.md](aegisai_text_injection_test/image_injection_test/cpu_based_image_test/COMMANDS.md), or use the interactive workflow in the [image evaluation guide](aegisai_text_injection_test/image_injection_test/README.md). The test is deliberately sequential: on CPU hardware, a smaller controlled experiment is more useful than an oversized run that cannot finish reliably.

#### What makes the CPU test research-quality

- **Controlled variables:** the corpus, attack prompt, defense prompt, model, sample limit, and timeout are explicit.
- **Comparable conditions:** `none`, `defense`, and `both` modes reuse the same evaluation path.
- **Reproducible evidence:** every run stores a command, UTC run ID, prompt configuration, prediction, confidence, latency, and errors.
- **Low-cost replication:** another student, reviewer, or hiring team member can reproduce the experiment on ordinary hardware.
- **Honest interpretation:** a small CPU sweep is labeled as a diagnostic study, and bypasses are preserved as limitations and follow-up work.

Open the generated CPU results from `aegisai_text_injection_test/image_injection_test/results/`. The most useful artifacts for a portfolio review are the attack catalog, the plain-language defense report, the offline dashboard, and the machine-readable JSON/CSV files.

### 4. Compare models

Install and start [Ollama](https://ollama.com), then run a selected model:

```powershell
.\run.cmd python src\run_tests.py --models "ollama:qwen2.5:0.5b" --timeout 120
```

For image-byte evaluation with a vision model:

```powershell
.\run.cmd python image_injection_test\src\run_tests.py --models "ollama:llava" --timeout 600
```

Selected missing Ollama models are downloaded automatically. Add `--no-download` to require that all models are already installed.

### 5. Generate reports

```powershell
.\run.cmd node src\generate_model_dashboard.js
.\run.cmd node src\generate_docx.js
.\run.cmd node src\generate_pptx.js
```

Open the generated files in the relevant `results/` directory. All reports are derived from the same JSON/CSV result data.

## Evidence and Results

The repository includes generated examples that make the evaluation process inspectable:

- [Text model comparison dashboard](aegisai_text_injection_test/results/model_comparison_dashboard.html)
- [Image attack and defense report](aegisai_text_injection_test/image_injection_test/results/attack_defense_report.html)
- [Image model comparison dashboard](aegisai_text_injection_test/image_injection_test/results/image_model_comparison_dashboard.html)
- [Layered defense attack catalog](aegisai_text_injection_test/image_injection_test/results/LAYERED_DEFENSE_ATTACK_CATALOG.md)
- [Latest image run report](aegisai_text_injection_test/image_injection_test/results/IMAGE_TEST_RUN_REPORT.md)
- [AI security project portfolio PDF](AI_SECURITY_PROJECT_PORTFOLIO.pdf)
- [Editable portfolio source](AI_SECURITY_PROJECT_PORTFOLIO.html)
- [LinkedIn project presentation PDF](LINKEDIN_PROJECT_PRESENTATION.pdf)
- [LinkedIn presentation source](LINKEDIN_PROJECT_PRESENTATION.html)
- [LinkedIn post text](LINKEDIN_POST.md)

The included image sweep is intentionally presented as a diagnostic sample, not as a universal benchmark. Its latest report documents eight attack types, model latency, detected attacks, bypasses, and limitations.

The [project portfolio PDF](aegisai_text_injection_test/results/AI_SECURITY_PROJECT_PORTFOLIO.pdf) is prepared for scholarship applications, CV/resume attachments, interviews, and project demonstrations. It includes a short project summary, technical architecture, evidence links, interview presentation script, scholarship statement, career-focused skills, and a future research roadmap. Regenerate it with `python src/generate_project_portfolio_pdf.py` from `aegisai_text_injection_test`.

## Documentation Guide

| Read this | When you need it |
| --- | --- |
| [Text evaluation guide](aegisai_text_injection_test/README.md) | Text corpus, model selection, providers, baselines, and report generation |
| [Image evaluation guide](aegisai_text_injection_test/image_injection_test/README.md) | Image corpora, OCR fallback, vision evaluation, custom image sets, and reports |
| [Image quick start](aegisai_text_injection_test/image_injection_test/README_QUICKSTART.md) | Short command-focused image workflow |
| [CPU image test guide](aegisai_text_injection_test/image_injection_test/cpu_based_image_test/README.md) | Low-memory profiles, experiment design, reports, and troubleshooting |
| [CPU command reference](aegisai_text_injection_test/image_injection_test/cpu_based_image_test/COMMANDS.md) | Copy-ready CPU-only commands and attack IDs |
| [Attack and defense guide](aegisai_text_injection_test/image_injection_test/README_ATTACK_DEFENSE.md) | Attack categories, defense modes, and interpretation |
| [Strict boundary catalog](aegisai_text_injection_test/image_injection_test/results/STRICT_BOUNDARY_ATTACK_CATALOG.md) | Detailed image attack outcomes and known bypasses |
| [Model testing guide](aegisai_text_injection_test/MODEL_TESTING.md) | Provider configuration, API keys, and comparison strategy |
| [Image-set guide](aegisai_text_injection_test/image_injection_test/image_sets/README.md) | Local folders, manifests, labels, and external image sources |

## Skills Shown

This project is a useful portfolio artifact because it connects several disciplines in one working system:

- Python CLI design and subprocess orchestration.
- JavaScript report generation and offline data visualization.
- JSON/CSV data contracts and reproducible experiment records.
- Prompt-injection threat modeling and defense taxonomy design.
- Multimodal input handling, OCR fallback, SVG/PNG rendering, and image manifests.
- Provider abstraction across local models and hosted APIs.
- Cross-platform setup for Windows, macOS, and Linux.
- Error handling, model timeouts, latency measurement, result archiving, and limitations reporting.

## Tools and Technologies

### AI Engineering

This project applies AI engineering principles to the security evaluation of language and vision models. It combines structured datasets, prompt design, model integration, deterministic testing, evaluation metrics, and reproducible reporting into one workflow.

The framework tests how AI systems distinguish trusted instructions from untrusted content embedded in text, images, OCR transcripts, documents, and other data sources.

### Large Language Models

The framework supports evaluation of multiple model providers and model types, including:

- Ollama local models.
- OpenAI models.
- Anthropic Claude models.
- Google Gemini models.
- Hugging Face models.
- OpenAI-compatible local servers.

Models are evaluated using consistent attack prompts, defense prompts, datasets, timeouts, and output metrics. This makes it possible to compare model behavior under the same conditions.

### AI Agents

The project includes simulated undefended and defended AI agents.

The undefended agent demonstrates how an AI system may incorrectly treat untrusted content as an instruction and attempt to execute an embedded action.

The defended agent separates trusted user or system instructions from untrusted text extracted from images or documents, potential tool calls, authority claims, safety bypass attempts, and data-exfiltration requests. This demonstrates how instruction boundaries can be implemented and evaluated before connecting an AI system to real tools.

### Prompt Engineering

The framework uses structured attack and defense prompt libraries. Attack prompts represent common prompt-injection techniques, including direct overrides, forged authority, delimiter escapes, role-play jailbreaks, urgency manipulation, fake tool responses, data exfiltration, and polite low-signal overrides.

Defense prompts instruct models to treat image and document content as untrusted data, classify it, and avoid following instructions embedded within it. The system also supports custom attack prompts, custom defense prompts, prompt overlays, and comparisons between different defense strategies.

### Multimodal AI

The image-testing component evaluates multimodal models that process image bytes directly. It supports image-embedded prompt injections, OCR and transcript-based evaluation, SVG/PNG/JPEG/WEBP/GIF/BMP inputs, local image folders, JSON image manifests, HTTP(S) image manifests, vision-capable Ollama models, and custom image labels.

The framework compares models that inspect actual image pixels with text-only models that use OCR or transcript data. This distinction helps identify whether a failure comes from visual understanding, OCR content, prompt handling, or the defense layer.

### AI Security and Evaluation

The project demonstrates practical AI security concepts, including threat modeling, trust-boundary design, prompt-injection detection, jailbreak analysis, tool-use safety, authority impersonation detection, data-exfiltration prevention, input validation, and limitations reporting.

The detector uses transparent pattern matching and weighted risk categories. Its decisions are expressed as `allow`, `hold`, or `block`, making the reasoning inspectable and suitable for experimentation.

The framework records attack detection rate, attack bypass or success rate, accuracy, false-positive rate, confidence, model errors, request latency, image-loading errors, successful calls, and failed calls. Each run also stores the command, model configuration, attack prompt, defense prompt, sample ID, run ID, and timestamp.

### Python

Python is used for command-line interfaces, dataset loading, corpus execution, agent simulation, heuristic detection, image processing, model-provider integration, Ollama model management, metrics collection, JSON/CSV result generation, and dependency bootstrapping.

Important Python components include:

- `bootstrap.py` for dependency and prerequisite setup.
- `agent.py` for undefended and defended agent simulations.
- `detector.py` for transparent prompt-injection detection.
- `model_eval.py` for provider adapters and model comparisons.
- `image_sets.py` for image folders, manifests, and URLs.
- `prompt_lab.py` for prompt selection and image overlays.
- `run_tests.py` for the main evaluation workflow.
- `select_model.py` for model catalog management.

### JavaScript and Node.js

Node.js is used to generate shareable evaluation artifacts, including offline HTML dashboards, DOCX reports, PDF reports, PowerPoint presentations, and Markdown attack catalogs. The JavaScript report generators transform machine-readable result files into artifacts that can be reviewed by researchers, instructors, recruiters, and security teams.

### Data and Experiment Design

The project uses versioned JSON corpora and structured result files. Input data includes attack samples, benign samples, image metadata, expected labels, attack categories, prompt libraries, model catalogs, and defense configurations.

Output data includes `results.json`, `results.csv`, `model_comparison.json`, `model_comparison.csv`, HTML dashboards, Markdown reports, DOCX files, PDF files, and PowerPoint files. This structure supports repeatable experiments, historical comparison, and future integration with automated analysis tools.

### Local and Hosted Model Integration

The provider abstraction allows the same evaluation workflow to work with local and hosted models.

Local models provide privacy, offline experimentation, lower recurring cost, reproducible CPU-based testing, and greater control over model versions. Hosted models provide access to larger models, cross-provider comparison, different reasoning and vision capabilities, and production-style API evaluation.

API keys are required only for hosted providers. Ollama models can run locally when Ollama is installed and running.

### CPU-Based AI Testing

The project includes a low-memory CPU testing workflow for users without a GPU:

- `8gb`: Moondream, one sample, 300-second timeout.
- `16gb`: Qwen 2.5 VL, two samples, 300-second timeout.
- `more`: LLaVA, four samples, 600-second timeout.

This makes the project easier to reproduce on ordinary laptops and educational computers. CPU testing also demonstrates responsible experiment design by limiting workload size, documenting hardware constraints, and avoiding unsupported performance claims. See the [CPU image test guide](aegisai_text_injection_test/image_injection_test/cpu_based_image_test/README.md) for the complete workflow.

### Reproducibility and Automation

The project provides cross-platform launchers: `run.cmd` for Windows and `run.sh` for macOS/Linux. The bootstrap system checks Python and Node.js versions, installs missing Python and Node.js packages, downloads selected missing Ollama models, and runs project commands from a consistent working directory.

Each experiment preserves historical results so that new runs do not silently overwrite earlier evidence.

### Portfolio and Career Relevance

This project demonstrates practical experience in AI engineering, LLM evaluation, AI agent safety, multimodal AI, prompt engineering, cybersecurity, Python development, JavaScript and Node.js, data engineering, experiment design, model benchmarking, technical documentation, cross-platform automation, and responsible AI development.

It is relevant to roles involving AI security, machine learning engineering, LLM applications, red teaming, evaluation engineering, software engineering, and responsible AI research.

## Scope and Responsible Use

This is a research and evaluation framework, not a guarantee that a model is secure. Results depend on the selected model, prompts, corpus, hardware, provider configuration, and test size. Bypasses are expected research findings. Do not connect the simulated tool actions to real external systems without authorization, isolation, logging, and human review.

The project intentionally includes attack examples so defenders can reproduce and measure failure modes. Use the corpus only in controlled testing environments and do not treat a successful small sweep as evidence of production readiness.

## Portfolio Summary

**One-line description:** Built a cross-platform, reproducible framework that measures text and image prompt-injection defenses across deterministic agents, local vision models, hosted providers, and structured attack corpora, with automatic setup and explainable reports.

**Research contribution:** Turns ambiguous prompt-injection behavior into repeatable experiments with explicit trusted/untrusted boundaries, measurable outcomes, archived runs, and documented limitations.

**Engineering contribution:** Connects data ingestion, heuristic detection, model adapters, dependency bootstrap, CLI workflows, and multi-format reporting into one runnable repository.

## License and Contributions

No license is currently declared in this repository. Add an explicit license before distributing the framework as reusable software. Contributions are welcome when they include a reproducible corpus or test case, a clear threat-model rationale, and updated documentation or result interpretation.