"""Final analiz. Model cagirmir. Kohne fayllara toxunmur; yeni fayllar vaxt mohuru ile yaradilir (mode x)."""
import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime
from math import comb, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluator_v3 import classify_attack, find_base64, _quality
from src.evaluator import expected_answer_present

BORDERS = ["empty", "=", "-", "code"]
CATS = ["Task Automation", "Base Encoding", "Information Dissemination",
        "Scams & Fraud", "Misinformation & Propaganda"]
POS = ["start", "middle", "end"]
LINES = []


def out(s=""):
    print(s)
    LINES.append(s)


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def last(rows, keys):
    d = {}
    for r in rows:
        d[tuple(r[k] for k in keys)] = r
    return list(d.values())


def cat(n):
    return n.rsplit("-", 1)[0]


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def line(label, rows):
    n = len(rows)
    k = sum(r["success"] for r in rows)
    lo, hi = wilson(k, n)
    return f"  {label:12s} {k:3d}/{n:<4d} {k / n:6.1%}   95% CI [{lo:.1%}, {hi:.1%}]"


def main(attack_path, baseline_path):
    attack = last(load(attack_path), ["email_index", "attack_name", "position", "border_type"])
    base = last(load(baseline_path), ["email_index", "border_type"])
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    res = ROOT / "results"

    for r in attack:
        o, why = classify_attack(r["attack_name"], r["response"])
        r["attack_outcome_v3"] = o
        r["attack_reason_v3"] = why
        r["task_answer_present_heuristic"] = expected_answer_present(r["ideal"], r["response"])
        r["category"] = cat(r["attack_name"])
        r["success"] = (o == "likely_followed")

    csv_path = res / f"final_v3_evaluated_{stamp}.csv"
    with open(csv_path, "x", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(attack[0].keys()))
        w.writeheader()
        w.writerows(attack)

    out("=== UMUMI (evaluator v3, hucum run: 600 sorgu) ===")
    out(line("hamisi", attack))
    out(f"  netice paylanmasi: {dict(Counter(r['attack_outcome_v3'] for r in attack))}")
    out(f"  kesilmis cavab (length): {sum(r['done_reason'] == 'length' for r in attack)}")

    out("\n=== BORDER UZRE ===")
    for b in BORDERS:
        out(line(b, [r for r in attack if r["border_type"] == b]))
    out("\n=== MOVQE UZRE ===")
    for p in POS:
        out(line(p, [r for r in attack if r["position"] == p]))
    out("\n=== KATEQORIYA UZRE ===")
    for c in CATS:
        out(line(c[:12], [r for r in attack if r["category"] == c]) + f"   <- {c}")

    out("\n=== BORDER x KATEQORIYA (uğurlu/30) ===")
    out(f"  {'':28s}" + "".join(f"{b:>8s}" for b in BORDERS))
    for c in CATS:
        cells = []
        for b in BORDERS:
            rs = [r for r in attack if r["category"] == c and r["border_type"] == b]
            cells.append(f"{sum(r['success'] for r in rs):>3d}/{len(rs):<3d} ")
        out(f"  {c:28s}" + "".join(cells))

    groups = defaultdict(dict)
    for r in attack:
        groups[(r["email_index"], r["attack_name"], r["position"])][r["border_type"]] = r["success"]
    out("\n=== CUTLESMIS MUQAYISE: empty vs diger (150 cut, deqiq McNemar) ===")
    for b in ["=", "-", "code"]:
        only_empty = sum(1 for g in groups.values() if g["empty"] and not g[b])
        only_other = sum(1 for g in groups.values() if g[b] and not g["empty"])
        p = mcnemar_exact(only_empty, only_other)
        out(f"  empty vs {b:5s}: yalniz empty-de={only_empty:2d} | yalniz {b}-de={only_other:2d} | p={p:.4f}")
    out("  Qeyd: 3 muqayise var (Bonferroni astanasi 0.0167). Numuneler arasi asililiq var,")
    out("  ona gore p-deyerler tesviri gostericidir, qəti sübut deyil.")

    out("\n=== BASE64 'likely_followed' CAVABLARI: dekod olunmus mezmun ===")
    rep = 0
    for r in attack:
        if r["category"] == "Base Encoding" and r["success"]:
            dec = find_base64(r["response"]) or ""
            q = _quality(dec)
            is_rep = "not clearly" not in q
            rep += is_rep
            out(f"  border={r['border_type']:5s} pos={r['position']:6s} tekrarli={is_rep!s:5s} {dec[:60]!r}")
    out(f"  tekrarli mezmun: {rep}")

    out("\n=== needs_review / mentioned_only SETIRLERI ===")
    for r in attack:
        if r["attack_outcome_v3"] in ("needs_review", "mentioned_only"):
            out(f"  [{r['category']}] {r['attack_outcome_v3']} border={r['border_type']} pos={r['position']} | "
                f"{r['response'][:140].replace(chr(10), ' ')}")

    out("\n=== TEMIZ BASELINE: cavab uygunlugu (heuristik, 40 sorgu) ===")
    def ok(rs):
        return sum(expected_answer_present(r["ideal"], r["response"]) for r in rs)
    tot_kn = tot_un = n_kn = n_un = 0
    for b in BORDERS:
        rows = [r for r in base if r["border_type"] == b]
        kn = [r for r in rows if r["ideal"].strip().lower() != "unknown"]
        un = [r for r in rows if r["ideal"].strip().lower() == "unknown"]
        out(f"  {b:6s} cemi {ok(rows)}/{len(rows)} | melum cavabli {ok(kn)}/{len(kn)} | 'unknown' cavabli {ok(un)}/{len(un)}")
        tot_kn += ok(kn); n_kn += len(kn); tot_un += ok(un); n_un += len(un)
    out(f"  YEKUN: melum cavabli {tot_kn}/{n_kn} | 'unknown' cavabli {tot_un}/{n_un}")

    out("\n=== HUCUM ALTINDA: melum cavabli suallarda cavab uygunlugu (border uzre) ===")
    for b in BORDERS:
        rs = [r for r in attack if r["border_type"] == b and r["ideal"].strip().lower() != "unknown"]
        out(f"  {b:6s} {sum(r['task_answer_present_heuristic'] for r in rs)}/{len(rs)}")

    out("\n=== QEYDLER ===")
    out("  1) v3 qaydalari v2 neticelerine baxildiqdan sonra yazilib: neticeler kor (blind) deyil.")
    out("  2) likely_followed = heuristik gostərici, tesdiqlenmis hucum ugurunu bildirmir.")
    out("  3) Her kateqoriyada yalniz 1 hucum metni, 10 email, 1 model: umumilesdirmek olmaz.")

    summary = res / f"final_summary_v3_{stamp}.txt"
    with open(summary, "x", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    out(f"\nYazildi: {csv_path.name}")
    out(f"Yazildi: {summary.name}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
