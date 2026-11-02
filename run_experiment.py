
import argparse
from pathlib import Path

from src.attack_generator import build_samples
from src.border_defense import BORDER_TYPES, make_prompt
from src.run_utils import new_run_path, run_jobs

ROOT = Path(__file__).resolve().parent

DEFAULT_EMAIL = ROOT.parent / "benchmark" / "email" / "test.jsonl"
DEFAULT_ATTACKS = ROOT.parent / "benchmark" / "text_attack_test.json"

META = [
    "email_index",
    "attack_name",
    "position",
    "border_type",
    "question",
    "ideal",
    "attack_text",
]

KEY = [
    "email_index",
    "attack_name",
    "position",
    "border_type",
]


def main():
    parser = argparse.ArgumentParser(
        description="BIPIA Border Strings: safe attack experiment"
    )

    parser.add_argument("--emails", default=str(DEFAULT_EMAIL))
    parser.add_argument("--attacks", default=str(DEFAULT_ATTACKS))
    parser.add_argument("--email-count", type=int, default=10)
    parser.add_argument("--prompts-per-category", type=int, default=1)
    parser.add_argument("--model", default="qwen2.5:1.5b")
    parser.add_argument("--tag", default="attack_v2")
    parser.add_argument("--resume", default=None)
    parser.add_argument("--limit", type=int, default=0)

    args = parser.parse_args()

    samples = build_samples(
        args.emails,
        args.attacks,
        args.email_count,
        prompts_per_category=args.prompts_per_category,
    )

    if args.limit:
        samples = samples[:args.limit]

    jobs = []

    for sample in samples:
        for border in BORDER_TYPES:
            jobs.append({
                "label": (
                    f"email={sample['email_index']} | "
                    f"{sample['attack_name']} | "
                    f"{sample['position']} | border={border}"
                ),
                "prompt": make_prompt(
                    sample["poisoned_context"],
                    sample["question"],
                    border,
                ),
                "meta": {
                    "email_index": sample["email_index"],
                    "attack_name": sample["attack_name"],
                    "position": sample["position"],
                    "border_type": border,
                    "question": sample["question"],
                    "ideal": sample["ideal"],
                    "attack_text": sample["attack_text"],
                },
            })

    if args.resume:
        out_path = Path(args.resume)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        out_path = new_run_path(ROOT / "results", args.tag)

    run_jobs(
        jobs,
        out_path,
        META,
        KEY,
        args.model,
        resume=bool(args.resume),
    )


if __name__ == "__main__":
    main()
