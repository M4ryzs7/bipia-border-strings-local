# Research Notes: BIPIA Border Strings Small Local Replication

## Research question
Do simple textual boundaries around untrusted email content change how often a local language model appears to follow indirect instructions embedded in that content?

## Conditions
- Baseline: `empty`
- Border Strings: `=`, `-`, `code`
- Same email, attack prompt, insertion position, and local model across conditions.

## Dataset subset
Default run: 2 emails × 5 selected attack prompts × 3 insertion positions = 30 poisoned inputs; each is evaluated under 4 border variants = 120 model calls.

## Metrics
- Heuristic attack-success flag: pattern-based screening for visible signs of following the selected attack.
- Task-answer-present flag: simple check for expected answer text or an `unknown`/no-information response.

These are preliminary proxy metrics. They are not equivalent to BIPIA's original model-based evaluator or a validated semantic evaluation.

## Limitations
- The target model is Qwen2.5 1.5B via Ollama, not GPT-3.5.
- The test subset is intentionally small.
- The heuristic evaluator can produce false positives and false negatives.
- A clean, non-attacked control evaluation should be run before making claims about benign task utility.
- Findings are exploratory and should not be represented as an exact reproduction of the paper's reported results.
