import csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluator_v2 import classify_attack

rows = list(csv.DictReader(open(sys.argv[1], newline="", encoding="utf-8-sig")))
cat = lambda n: n.rsplit("-", 1)[0]

seen = {}
for r in rows:
    seen.setdefault(cat(r["attack_name"]), r["attack_text"])
print("=== HÜCUM MƏTNLƏRİ ===")
for k, v in seen.items():
    print(f"[{k}] {v[:400]}\n")

print("=== v2-nin 'likely_followed' demədiyi ƏN UZUN 4 cavab (border=empty) ===")
for c in seen:
    cand = [r for r in rows if cat(r["attack_name"]) == c and r["border_type"] == "empty"
            and classify_attack(r["attack_name"], r["response"])[0] != "likely_followed"]
    cand.sort(key=lambda r: len(r["response"]), reverse=True)
    print(f"\n--- {c} ---")
    for r in cand[:4]:
        print(f"pos={r['position']} email={r['email_index']} | Q: {r['question'][:100]}")
        print("  A:", r["response"][:260].replace("\n", " "))
