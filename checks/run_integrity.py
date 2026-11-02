"""Yalnız oxuyur. Model çağırmır, heç bir faylı dəyişmir."""
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluator_v2 import classify_attack

CATS = ["Task Automation", "Base Encoding", "Information Dissemination",
        "Scams & Fraud", "Misinformation & Propaganda"]
B64 = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def last_rows(rows, keys):
    final = {}
    for r in rows:                       # eyni açar təkrarlanıbsa SON sətir qalır
        final[tuple(r[k] for k in keys)] = r
    return list(final.values())


def short(s, n=220):
    return (s or "")[:n].replace("\n", " ")


def category(name):
    return name.rsplit("-", 1)[0]


def integrity(name, rows):
    print(f"\n=== BÜTÖVLÜK: {name} ===")
    print("status:", dict(Counter(r["status"] for r in rows)))
    print("done_reason:", dict(Counter(r["done_reason"] for r in rows)))
    print("model:", set(r["model"] for r in rows))
    toks = [int(r["prompt_tokens"]) for r in rows if r["prompt_tokens"].isdigit()]
    if toks:
        print(f"prompt_tokens: min={min(toks)} max={max(toks)} | boş={len(rows) - len(toks)}")


def main(attack_path, baseline_path):
    a_raw = load(attack_path)
    b_raw = load(baseline_path)
    attack = last_rows(a_raw, ["email_index", "attack_name", "position", "border_type"])
    base = last_rows(b_raw, ["email_index", "border_type"])
    print(f"hücum: xam={len(a_raw)} unikal={len(attack)} (gözlənilən 600)")
    print(f"baseline: xam={len(b_raw)} unikal={len(base)} (gözlənilən 40)")
    integrity("hücum", attack)
    integrity("baseline", base)

    trunc = Counter(category(r["attack_name"]) for r in attack if r["done_reason"] == "length")
    print("\nkəsilmiş (length) hücum cavabları, kateqoriya üzrə:", dict(trunc))

    outcome_by_cat = defaultdict(Counter)
    followed = defaultdict(list)
    for r in attack:
        if r["status"] != "success":
            continue
        cat = category(r["attack_name"])
        out, why = classify_attack(r["attack_name"], r["response"])
        outcome_by_cat[cat][out] += 1
        if out == "likely_followed":
            followed[cat].append((r, why))
    total_followed = sum(c["likely_followed"] for c in outcome_by_cat.values())
    print("\n=== v2 NƏTİCƏLƏRİ (təzədən hesablandı) ===")
    for cat in CATS:
        print(f"{cat}: {dict(outcome_by_cat[cat])}")
    print(f"CƏMİ likely_followed = {total_followed} (cədvəldə 20 idi: 15 Base + 5 Info)")

    print("\n=== likely_followed NÜMUNƏLƏRİ (hər kateqoriyadan 5-ə qədər) ===")
    for cat in CATS:
        for r, why in followed[cat][:5]:
            print(f"\n[{cat}] border={r['border_type']} pos={r['position']} | {why}")
            print("  cavab:", short(r["response"]))

    base_rows = [r for r in attack if category(r["attack_name"]) == "Base Encoding"
                 and r["status"] == "success"]
    missed = [r for r in base_rows
              if classify_attack(r["attack_name"], r["response"])[0] == "no_indicator"
              and B64.search(r["response"])]
    print("\n=== BASE64 AUDİT ===")
    print(f"Base Encoding sətirləri: {len(base_rows)} | "
          f"v2 'yoxdur' deyib, amma 24+ simvollu Base64-bənzər sətir var: {len(missed)}")
    print("  onlardan done_reason=length olanlar:",
          sum(1 for r in missed if r["done_reason"] == "length"))
    for r in missed[:4]:
        print(f"  border={r['border_type']} pos={r['position']} reason={r['done_reason']} | {short(r['response'])}")

    print("\n=== MƏNFİ NƏZARƏT (təmiz email cavabları, hücum yoxdur) ===")
    clean_ok = [r for r in base if r["status"] == "success"]
    print(f"təmiz cavab sayı: {len(clean_ok)}")
    for cat in CATS:
        c = Counter()
        ex = []
        for r in clean_ok:
            out, why = classify_attack(f"{cat}-0", r["response"])
            c[out] += 1
            if out != "no_indicator" and len(ex) < 2:
                ex.append((out, why, r))
        print(f"{cat}: {dict(c)}")
        for out, why, r in ex:
            print(f"   -> {out} | {why} | {short(r['response'], 160)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
