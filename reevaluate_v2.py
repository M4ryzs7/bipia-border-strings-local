
import csv
from collections import Counter, defaultdict
from pathlib import Path

from src.evaluator_v2 import classify_attack

ROOT = Path(__file__).resolve().parent

SOURCE = ROOT / "results" / "expanded_attack_results.csv"
OUTPUT = ROOT / "results" / "expanded_attack_results_v2_evaluated.csv"


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE}")

    if OUTPUT.exists():
        raise FileExistsError(
            f"Output already exists. Refusing to overwrite: {OUTPUT}"
        )

    with open(SOURCE, newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    if not rows:
        raise ValueError("Source CSV is empty.")

    required = {"attack_name", "response", "border_type"}
    if not required.issubset(fields):
        raise ValueError("Source CSV is missing required columns.")

    new_fields = fields + ["attack_outcome_v2", "attack_reason_v2"]

    border_stats = defaultdict(Counter)
    category_stats = defaultdict(Counter)
    total = Counter()

    for row in rows:
        if row.get("response", "").startswith("ERROR:"):
            outcome = "error"
            reason = "original inference error"
        else:
            outcome, reason = classify_attack(
                row["attack_name"],
                row["response"]
            )

        row["attack_outcome_v2"] = outcome
        row["attack_reason_v2"] = reason

        if outcome != "error":
            border_stats[row["border_type"]][outcome] += 1
            category = row["attack_name"].rsplit("-", 1)[0]
            category_stats[category][outcome] += 1
            total[outcome] += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "x", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=new_fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows: {len(rows)}")
    print(f"Errors: {sum(1 for r in rows if r['attack_outcome_v2'] == 'error')}")

    print("\n=== RESULTS BY BORDER ===")
    for border, counts in border_stats.items():
        n = sum(counts.values())
        rate = counts["likely_followed"] / n if n else 0
        print(
            f"{border}: likely_followed={counts['likely_followed']}/{n} "
            f"({rate:.1%}), mentioned_only={counts['mentioned_only']}, "
            f"no_indicator={counts['no_indicator']}"
        )

    print("\n=== RESULTS BY ATTACK ===")
    for category, counts in category_stats.items():
        n = sum(counts.values())
        rate = counts["likely_followed"] / n if n else 0
        print(
            f"{category}: likely_followed={counts['likely_followed']}/{n} "
            f"({rate:.1%}), mentioned_only={counts['mentioned_only']}, "
            f"no_indicator={counts['no_indicator']}"
        )

    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
