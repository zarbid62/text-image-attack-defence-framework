# CPU-Only Command Reference

Run from:

```powershell
cd "E:\download folder\download 3\aegisai_text_injection_test\aegisai_text_injection_test\image_injection_test"
```

## Check available models

```powershell
ollama list
python src\run_tests.py --image-models
```

## 8 GB RAM, safest option

```powershell
ollama pull moondream
python src\run_tests.py --cpu-only --cpu-profile 8gb --attack-prompt-id direct_override --overlay-attack-prompt --defense-mode defense --defense-prompt-id layered_defense
```

Equivalent explicit command:

```powershell
python src\run_tests.py --models "ollama:moondream" --max-samples 1 --attack-prompt-id direct_override --overlay-attack-prompt --defense-mode defense --defense-prompt-id layered_defense --timeout 300
```

## 16 GB RAM

```powershell
ollama pull qwen2.5vl:3b
python src\run_tests.py --cpu-only --cpu-profile 16gb --attack-prompt-id direct_override --overlay-attack-prompt --defense-mode defense --defense-prompt-id layered_defense
```

## More than 16 GB RAM

```powershell
ollama pull llava
python src\run_tests.py --cpu-only --cpu-profile more --attack-prompt-id direct_override --overlay-attack-prompt --defense-mode defense --defense-prompt-id layered_defense
```

## Compare without and with defense

Use only one image on an 8 GB CPU-only machine:

```powershell
python src\run_tests.py --cpu-only --cpu-profile 8gb --models "ollama:moondream" --max-samples 1 --attack-prompt-id direct_override --overlay-attack-prompt --defense-mode both --defense-prompt-id layered_defense --timeout 300
```

## Attack IDs

```text
direct_override
forged_authority
delimiter_escape
roleplay
urgency
tool_response
exfiltration
polite_override
```

Example for a single attack:

```powershell
python src\run_tests.py --cpu-only --cpu-profile 8gb --models "ollama:moondream" --max-samples 1 --attack-prompt-id forged_authority --overlay-attack-prompt --defense-mode defense --defense-prompt-id layered_defense --timeout 300
```

## Open reports

```powershell
Start-Process .\results\LAYERED_DEFENSE_ATTACK_CATALOG.md
Start-Process .\results\image_model_comparison_dashboard.html
Start-Process .\results\attack_defense_report.html
```

## Print the latest terminal summary

```powershell
python src\run_tests.py --capability-report
```
