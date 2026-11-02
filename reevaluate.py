
import sys
import pandas as pd

sys.path.insert(0, "border_strings_project")

from src.evaluator import (
    heuristic_attack_success,
    expected_answer_present
)

source = "border_strings_project/results/experiment_results.csv"
output = "border_strings_project/results/reevaluated_results.csv"

df = pd.read_csv(source)

results = [
    heuristic_attack_success(
        str(row["attack_name"]),
        str(row["response"])
    )
    for _, row in df.iterrows()
]

df["attack_success_heuristic"] = [x[0] for x in results]
df["attack_success_reason"] = [x[1] for x in results]

df["task_answer_present"] = [
    expected_answer_present(
        str(row["ideal"]),
        str(row["response"])
    )
    for _, row in df.iterrows()
]

df.to_csv(output, index=False, encoding="utf-8-sig")

print("Re-evaluation completed!")
print("Total samples:", len(df))

print("\n=== RESULTS BY BORDER ===")
print(
    df.groupby("border_type").agg(
        attack_success_rate=("attack_success_heuristic", "mean"),
        task_answer_rate=("task_answer_present", "mean"),
        samples=("email_index", "count")
    ).round(3)
)

print("\n=== RESULTS BY ATTACK ===")
print(
    df.groupby("attack_name")["attack_success_heuristic"]
    .agg(["sum", "count", "mean"])
    .round(3)
)

print("\nSaved:", output)
