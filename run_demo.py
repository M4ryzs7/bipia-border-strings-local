"""Demo: eyni hucum, 4 border, canli cavab (4 model cagirisi).
Cixis results/demo_<vaxt>.txt faylina yazilir (mode x, movcud fayla toxunulmur)."""
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.attack_generator import build_samples
from src.border_defense import BORDER_TYPES, make_prompt
from src.local_llm import generate_full
from src.evaluator_v3 import classify_attack

EMAILS = ROOT.parent / "benchmark" / "email" / "test.jsonl"
ATTACKS = ROOT.parent / "benchmark" / "text_attack_test.json"


def load_groups(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    groups = {}
    for r in rows:
        key = (r["email_index"], r["attack_name"], r["position"])
        groups.setdefault(key, {})[r["border_type"]] = r["attack_outcome_v3"]
    return groups


def pick_case(groups):
    cands = [k for k, g in groups.items()
             if g.get("empty") == "likely_followed"
             and g.get("=") != "likely_followed"
             and g.get("-") != "likely_followed"]
    cands.sort(key=lambda k: (not k[1].startswith("Information"), k))
    return cands[0] if cands else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("results_csv")
    p.add_argument("--email")
    p.add_argument("--attack")
    p.add_argument("--position")
    p.add_argument("--model", default="qwen2.5:1.5b")
    a = p.parse_args()

    groups = load_groups(a.results_csv)
    if a.email and a.attack and a.position:
        key = (a.email, a.attack, a.position)
    else:
        key = pick_case(groups)
    if key is None or key not in groups:
        raise SystemExit("Uygun hal tapilmadi. --email --attack --position verin.")

    samples = build_samples(str(EMAILS), str(ATTACKS), 10, prompts_per_category=1)
    s = next(x for x in samples
             if str(x["email_index"]) == key[0]
             and x["attack_name"] == key[1]
             and x["position"] == key[2])

    lines = []

    def out(t=""):
        print(t)
        lines.append(t)

    out(f"DEMO | email={key[0]} | hucum={key[1]} | movqe={key[2]} | model={a.model}")
    out(f"Sual: {s['question']}")
    out(f"Hucum metni: {s['attack_text']}")
    out("Evaluator: v3 (heuristik gosterici; tesdiqlenmis hucum ugurunu bildirmir)")
    out("-" * 70)
    for border in BORDER_TYPES:
        prompt = make_prompt(s["poisoned_context"], s["question"], border)
        r = generate_full(prompt, model=a.model)
        outcome, why = classify_attack(s["attack_name"], r["text"])
        stored = groups[key].get(border, "?")
        out(f"[border={border}] canli netice: {outcome} | final run-da: {stored}")
        out(f"  cavab: {r['text'][:300]!r}")
        out()
    out("Qeyd: temperature=0, amma Ollama cavablari nadir hallarda final run-dan ferqlene biler.")

    path = ROOT / "results" / f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(path, "x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nYazildi: {path.name}")


if __name__ == "__main__":
    main()
