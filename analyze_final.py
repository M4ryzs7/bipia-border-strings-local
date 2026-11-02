import pandas as pd
from pathlib import Path
from src.evaluator_v2 import classify_attack

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

ATTACK_FILE = RESULTS / "attack_final_20261102_113040.csv"
BASELINE_FILE = RESULTS / "baseline_final_20261102_120205.csv"

attack = pd.read_csv(ATTACK_FILE)
baseline = pd.read_csv(BASELINE_FILE)

# 1. Attack experiment evaluation
evaluations = attack.apply(
    lambda row: classify_attack(row["attack_name"], row["response"]),
    axis=1
)

attack["attack_outcome"] = [x[0] for x in evaluations]
attack["attack_reason"] = [x[1] for x in evaluations]

attack_output = RESULTS / "attack_final_evaluated.csv"
attack.to_csv(attack_output, index=False, encoding="utf-8-sig")

print("\n=== ATTACK RESULTS BY BORDER ===")
print(
    attack.groupby(["border_type", "attack_outcome"])
    .size().unstack(fill_value=0)
)

print("\n=== ATTACK SUCCESS RATE BY BORDER ===")
print(
    attack.assign(
        likely_followed=attack["attack_outcome"].eq("likely_followed")
    )
    .groupby("border_type")["likely_followed"]
    .agg(["sum", "count", "mean"])
)

print("\n=== RESULTS BY ATTACK CATEGORY ===")
print(
    attack.assign(
        category=attack["attack_name"].str.rsplit("-", n=1).str[0],
        likely_followed=attack["attack_outcome"].eq("likely_followed")
    )
    .groupby("category")["likely_followed"]
    .agg(["sum", "count", "mean"])
)

print("\n=== RESULTS BY POSITION ===")
print(
    attack.assign(
        likely_followed=attack["attack_outcome"].eq("likely_followed")
    )
    .groupby("position")["likely_followed"]
    .agg(["sum", "count", "mean"])
)

# 2. Clean baseline summary
print("\n=== CLEAN BASELINE BY BORDER ===")
print(
    baseline.groupby("border_type")
    .agg(
        responses=("response", "count"),
        avg_latency=("elapsed_seconds", "mean")
    )
)

print("\n=== BASELINE IDEAL ANSWERS ===")
print(baseline[["border_type", "ideal", "response"]].to_string(index=False))

print("\nSaved:", attack_output)
print("Baseline source:", BASELINE_FILE)