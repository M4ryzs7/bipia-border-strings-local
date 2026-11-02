
import argparse
from pathlib import Path

from src.attack_generator import load_jsonl
from src.border_defense import BORDER_TYPES, make_prompt
from src.run_utils import new_run_path, run_jobs

ROOT = Path(__file__).resolve().parent

DEFAULT_EMAIL = ROOT.parent / "benchmark" / "email" / "test.jsonl"

META = [
    "email_index",
    "border_type",
    "question",
    "ideal",
]

KEY = [
    "email_index",
    "border_type",
]


def main():
    parser = argparse.ArgumentParser(
        description="BIPIA Border Strings: safe clean baseline"
    )

    parser.add_argument("--emails", default=str(DEFAULT_EMAIL))
    parser.add_argument("--email-count", type=int, default=10)
    parser.add_argument("--model", default="qwen2.5:1.5b")
    parser.add_argument("--tag", default="baseline_v2")
    parser.add_argument("--resume", default=None)

    args = parser.parse_args()

    emails = load_jsonl(args.emails)[:args.email_count]

    jobs = []

    for index, email in enumerate(emails):
        for border in BORDER_TYPES:
            jobs.append({
                "label": f"email={index} | border={border}",
                "prompt": make_prompt(
                    email["context"],
                    email["question"],
                    border,
                ),
                "meta": {
                    "email_index": index,
                    "border_type": border,
                    "question": email["question"],
                    "ideal": email["ideal"],
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
