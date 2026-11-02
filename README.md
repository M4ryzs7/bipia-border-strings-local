# BIPIA Border Strings — Small Local Replication

This project reproduces the **Border Strings prompt-formatting defense** from Microsoft's BIPIA repository on a small, local subset using Ollama.

## What is preserved
- BIPIA email test data and text-attack prompts are read from the original repository.
- The four border variants (`empty`, `=`, `-`, `code`) follow the `add_border()` logic in `defense/black_box/few_shot.py`.
- The three attack positions are represented: start, middle, end.
- The email-assistant prompt is based on `bipia/data/email.py`.

## What is adapted
- Original GPT-3.5 inference is replaced by local `qwen2.5:1.5b` through Ollama.
- The original BIPIA evaluation uses model-based evaluators; this prototype uses transparent keyword/pattern heuristics for an initial screening only.
- The small default run uses 2 emails, 5 selected attack categories (first prompt from each), 3 positions, and 4 border variants: 2 × 5 × 3 × 4 = 120 inference calls.

## Requirements
- Windows + Python 3.10+ (tested target: Python 3.13)
- Ollama installed and running
- `ollama pull qwen2.5:1.5b`
- Python dependency: `requests`

## Run from the original BIPIA repository
Place this folder at `C:\TKS\BIPIA\border_strings_project`.

```powershell
cd C:\TKS\BIPIA
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\border_strings_project\requirements.txt
python .\border_strings_project\run_experiment.py
```

The script expects original BIPIA data at:
- `C:\TKS\BIPIA\benchmark\email\test.jsonl`
- `C:\TKS\BIPIA\benchmark\text_attack_test.json`

Results are written to `results/experiment_results.csv`.

## Faster pilot
To run only the first 6 poisoned samples (24 calls):
```powershell
python .\border_strings_project\run_experiment.py --limit 6
```

To use more emails or all five prompts in each selected category:
```powershell
python .\border_strings_project\run_experiment.py --email-count 5 --prompts-per-category 2
```

## Important interpretation
`attack_success_heuristic` is a **heuristic flag**, not a validated semantic attack-success judgment. Inspect the `response` column manually before reporting ASR. `task_answer_present` is also a simple exact/unknown phrase check, not a full semantic correctness score. Do not present these as directly comparable to the original paper's GPT-4-evaluated ASR.

## Research checklist
1. Run the experiment.
2. Inspect responses for each attack and border.
3. Manually adjudicate ambiguous heuristic flags.
4. Report model, quantization/runtime, sample size, attack subset, positions, border variants, and evaluator limitations.
5. Include clean (non-poisoned) task accuracy separately before making claims about utility impact.
