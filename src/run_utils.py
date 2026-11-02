
import csv
import time
from datetime import datetime
from pathlib import Path

from src.local_llm import generate_full

MAX_CONSECUTIVE_ERRORS = 5

RESULT_FIELDS = [
    "model",
    "response",
    "status",
    "done_reason",
    "prompt_tokens",
    "output_tokens",
    "elapsed_seconds",
]


def new_run_path(results_dir: Path, tag: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(results_dir) / f"{tag}_{stamp}.csv"


def run_jobs(jobs, out_path, meta_fields, key_fields, model, resume=False):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(meta_fields) + RESULT_FIELDS

    def make_key(meta):
        return tuple(str(meta[k]) for k in key_fields)

    done = set()

    if resume:
        if not out_path.exists():
            raise SystemExit(f"Resume file not found: {out_path}")

        with open(out_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames != fields:
                raise SystemExit("CSV columns do not match the expected format.")

            for row in reader:
                if row["status"] == "success":
                    done.add(tuple(row[k] for k in key_fields))

        f = open(out_path, "a", newline="", encoding="utf-8-sig")

    else:
        if out_path.exists():
            raise SystemExit(f"File already exists; refusing to overwrite: {out_path}")

        f = open(out_path, "x", newline="", encoding="utf-8-sig")
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        f.flush()

    writer = csv.DictWriter(f, fieldnames=fields)

    pending = [job for job in jobs if make_key(job["meta"]) not in done]

    print(f"Total jobs: {len(jobs)}")
    print(f"Previously successful: {len(done)}")
    print(f"Remaining: {len(pending)}")
    print(f"Output: {out_path}")

    errors_in_row = 0
    finished = False

    try:
        for number, job in enumerate(pending, 1):
            started = time.time()

            row = dict(job["meta"])
            row["model"] = model

            try:
                result = generate_full(job["prompt"], model=model)

                row.update({
                    "response": result["text"],
                    "status": "success",
                    "done_reason": result["done_reason"],
                    "prompt_tokens": result["prompt_tokens"],
                    "output_tokens": result["output_tokens"],
                })

                errors_in_row = 0

            except Exception as exc:
                row.update({
                    "response": f"ERROR: {exc}",
                    "status": "error",
                    "done_reason": "",
                    "prompt_tokens": "",
                    "output_tokens": "",
                })

                errors_in_row += 1

            row["elapsed_seconds"] = round(time.time() - started, 2)

            writer.writerow(row)
            f.flush()

            print(
                f"[{number}/{len(pending)}] "
                f"{job['label']} | {row['status']} | "
                f"{row['elapsed_seconds']}s"
            )

            if errors_in_row >= MAX_CONSECUTIVE_ERRORS:
                print("Five consecutive errors. Stopping.")
                break

        else:
            finished = True

    except KeyboardInterrupt:
        print("\nInterrupted. Completed rows have been saved.")

    finally:
        f.close()

    if finished:
        print(f"\nExperiment completed: {out_path}")
    else:
        print(f"\nExperiment incomplete. Resume using: {out_path}")

    return finished
