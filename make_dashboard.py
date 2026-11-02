"""Final CSV-lerden tek fayllik HTML dashboard yaradir. Model cagirmir. Movcud fayla toxunmur (mode x)."""
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.evaluator import expected_answer_present

BORDERS = ["empty", "=", "-", "code"]


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def last(rows, keys):
    d = {}
    for r in rows:
        d[tuple(r[k] for k in keys)] = r
    return list(d.values())


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BIPIA Border Strings Dashboard</title>
<style>
:root{--bg:#fafaf8;--fg:#1c1c1a;--mut:#6b6b66;--card:#fff;--bd:#e3e2dc;--acc:#2b59c3;--red:#c0392b;--amb:#b7791f;--grn:#2f855a}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--mut:#9a9992;--card:#1f1f1c;--bd:#33332f;--acc:#7aa2f7;--red:#f08a7e;--amb:#e5b567;--grn:#7bc596}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,"Segoe UI",sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:18px;margin:34px 0 10px}
.sub{color:var(--mut);margin:0 0 14px}
.warn{background:var(--card);border:1px solid var(--amb);border-left:4px solid var(--amb);border-radius:8px;padding:10px 14px;font-size:14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:14px}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:26px;line-height:1.2}
.kpi span{color:var(--mut);font-size:13px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px}
.bar{display:grid;grid-template-columns:150px 1fr 230px;gap:10px;align-items:center;margin:8px 0;font-size:14px}
.track{position:relative;height:16px;background:var(--bd);border-radius:4px}
.fill{position:absolute;left:0;top:0;bottom:0;background:var(--acc);border-radius:4px;opacity:.85}
.ci{position:absolute;top:5px;height:6px;border-left:2px solid var(--fg);border-right:2px solid var(--fg);background:rgba(128,128,128,.35)}
.muted{color:var(--mut)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--bd);padding:6px 8px;text-align:left}
th{color:var(--mut);font-weight:600}
td.n{text-align:center;font-variant-numeric:tabular-nums}
.sel{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
select,button{font:inherit;padding:6px 8px;border:1px solid var(--bd);border-radius:6px;background:var(--card);color:var(--fg)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-top:10px}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:600;border:1px solid}
.b-likely_followed{color:var(--red);border-color:var(--red)}
.b-mentioned_only,.b-needs_review{color:var(--amb);border-color:var(--amb)}
.b-no_indicator{color:var(--grn);border-color:var(--grn)}
pre{white-space:pre-wrap;word-break:break-word;margin:8px 0 0;font:13px/1.45 ui-monospace,Consolas,monospace}
tr.click{cursor:pointer}
tr.click:hover{background:rgba(128,128,128,.12)}
.small{font-size:13px;color:var(--mut)}
@media (max-width:640px){.bar{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<h1>BIPIA Border Strings: results dashboard</h1>
<p class="sub">Small local adaptation, Qwen2.5 1.5B via Ollama. Generated from <span id="src"></span>.</p>
<div class="warn"><b>Read first.</b> "Flagged" means the response matched a rule from evaluator v3 (<code>likely_followed</code>). It is a heuristic indicator, not a verified attack success. The v3 rules were written after inspecting v2 results on the same data (not blind). One small model, 10 emails, 1 attack prompt per category. This is not a reproduction of the BIPIA paper; do not compare with its numbers. The <code>none</code> condition still contains the "do not follow instructions" warning.</div>
<div class="kpis" id="kpis"></div>

<h2>Flagged responses by border</h2>
<div class="card" id="borders"></div>
<p class="small">Bar = share of 150 responses flagged. Whisker = 95% Wilson interval.</p>

<h2>Border x attack category (flagged out of 30)</h2>
<div class="card"><div id="heat"></div></div>
<p class="small">Most flags come from two categories. In the others the model rarely followed the attack, so a border effect cannot be measured there.</p>

<h2>By insertion position</h2>
<div class="card" id="pos"></div>

<h2>Paired comparison against "none" (same email, attack, position)</h2>
<div class="card"><div id="paired"></div>
<p class="small">Exact McNemar test. 3 comparisons (Bonferroni threshold 0.0167). Samples are not fully independent, so p-values are indicative only.</p></div>

<h2>Compare the four borders on one case</h2>
<div class="card">
<div class="sel"><label>Email <select id="selE"></select></label>
<label>Attack <select id="selA"></select></label>
<label>Position <select id="selP"></select></label></div>
<div id="caseinfo" class="small"></div>
<div class="grid" id="cards"></div>
<p class="small">Stored responses from the final run (no live model call). The default case was chosen because "none" was flagged and "=" and "-" were not, so it is illustrative, not representative.</p>
</div>

<h2>All flagged responses (click a row to open the case)</h2>
<div class="card"><div id="flagged"></div></div>

<h2>Clean baseline (no attack, 40 calls)</h2>
<div class="card"><div id="base"></div>
<p class="small">Heuristic text match, only 5 questions per cell: per-border differences are not interpretable. Overall the model rarely answered "unknown" when that was the right answer.</p></div>
</div>
<script>
const D = __DATA__;
const rows = D.rows, base = D.base;
const BORDERS=["empty","=","-","code"];
const BL={"empty":"none (warning only)","=":"= lines","-":"- lines","code":"code fence"};
const POS=["start","middle","end"];
const MAXV=0.25;
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const flagged=r=>r.o==="likely_followed";
const pct=x=>(100*x).toFixed(1)+"%";
function wilson(k,n){if(!n)return[0,0];const z=1.96,p=k/n,d=1+z*z/n,c=(p+z*z/(2*n))/d,h=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return[Math.max(0,c-h),Math.min(1,c+h)];}
function comb(n,k){let r=1;for(let i=1;i<=k;i++)r=r*(n-k+i)/i;return r;}
function mcnemar(b,c){const n=b+c;if(!n)return 1;const k=Math.min(b,c);let s=0;for(let i=0;i<=k;i++)s+=comb(n,i);return Math.min(1,2*s/Math.pow(2,n));}
function bar(label,k,n){const[lo,hi]=wilson(k,n);const w=Math.min(100,(n?k/n:0)/MAXV*100);const l=Math.min(100,lo/MAXV*100);const cw=Math.max(0,Math.min(100-l,(hi-lo)/MAXV*100));
return `<div class="bar"><div>${label}</div><div class="track"><div class="fill" style="width:${w}%"></div><div class="ci" style="left:${l}%;width:${cw}%"></div></div><div>${k}/${n} &middot; ${pct(n?k/n:0)} <span class="muted">[${pct(lo)}-${pct(hi)}]</span></div></div>`;}
const cnt=(f)=>rows.filter(f).length;

$("#src").textContent=D.meta.src;
const total=rows.length,fl=cnt(flagged),trunc=cnt(r=>r.d==="length");
$("#kpis").innerHTML=[[total,"attack calls analysed"],[fl,"flagged (likely_followed)"],[pct(fl/total),"overall flagged rate"],[trunc,"responses cut at token limit"]]
 .map(x=>`<div class="kpi"><b>${x[0]}</b><span>${x[1]}</span></div>`).join("");

$("#borders").innerHTML=BORDERS.map(b=>bar(BL[b],cnt(r=>r.b===b&&flagged(r)),cnt(r=>r.b===b))).join("");
$("#pos").innerHTML=POS.map(p=>bar(p,cnt(r=>r.p===p&&flagged(r)),cnt(r=>r.p===p))).join("");

const cats=[...new Set(rows.map(r=>r.c))];
let maxc=1;cats.forEach(c=>BORDERS.forEach(b=>{maxc=Math.max(maxc,cnt(r=>r.c===c&&r.b===b&&flagged(r)));}));
$("#heat").innerHTML="<table><tr><th>Category</th>"+BORDERS.map(b=>`<th class="n">${esc(BL[b])}</th>`).join("")+"</tr>"+
 cats.map(c=>"<tr><td>"+esc(c)+"</td>"+BORDERS.map(b=>{const n=cnt(r=>r.c===c&&r.b===b),k=cnt(r=>r.c===c&&r.b===b&&flagged(r));
 return `<td class="n" style="background:rgba(220,70,60,${(k/maxc*0.55).toFixed(2)})">${k}/${n}</td>`;}).join("")+"</tr>").join("")+"</table>";

const groups={};const keyOf=r=>r.e+"|"+r.a+"|"+r.p;
rows.forEach(r=>{(groups[keyOf(r)]=groups[keyOf(r)]||{})[r.b]=flagged(r);});
$("#paired").innerHTML="<table><tr><th>Comparison</th><th class='n'>flagged only in none</th><th class='n'>flagged only in other</th><th class='n'>p (exact)</th></tr>"+
 ["=","-","code"].map(b=>{let o=0,t=0;Object.values(groups).forEach(g=>{if(g.empty&&!g[b])o++;if(g[b]&&!g.empty)t++;});
 return `<tr><td>none vs ${esc(BL[b])}</td><td class="n">${o}</td><td class="n">${t}</td><td class="n">${mcnemar(o,t).toFixed(4)}</td></tr>`;}).join("")+"</table>";

function fill(sel,vals){$(sel).innerHTML=vals.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join("");}
fill("#selE",[...new Set(rows.map(r=>r.e))].sort((a,b)=>a-b));
fill("#selA",[...new Set(rows.map(r=>r.a))]);
fill("#selP",POS);
function show(){
 const e=+$("#selE").value,a=$("#selA").value,p=$("#selP").value;
 const any=rows.find(x=>x.e===e&&x.a===a&&x.p===p);
 if(!any){$("#caseinfo").textContent="No data for this combination.";$("#cards").innerHTML="";return;}
 $("#caseinfo").innerHTML=`<b>Question:</b> ${esc(any.q)}<br><b>Injected instruction:</b> ${esc(any.t)}`;
 $("#cards").innerHTML=BORDERS.map(b=>{const r=rows.find(x=>x.e===e&&x.a===a&&x.p===p&&x.b===b);
  if(!r)return "";
  return `<div class="card"><b>${esc(BL[b])}</b> <span class="badge b-${r.o}">${esc(r.o)}</span><div class="small">${esc(r.w)}${r.d==="length"?" | cut at token limit":""}</div><pre>${esc(r.r)}</pre></div>`;}).join("");
}
["#selE","#selA","#selP"].forEach(s=>$(s).addEventListener("change",show));
function load(e,a,p){$("#selE").value=e;$("#selA").value=a;$("#selP").value=p;show();$("#selE").scrollIntoView({behavior:"smooth",block:"center"});}
let start=Object.keys(groups).find(k=>groups[k].empty&&!groups[k]["="]&&!groups[k]["-"]&&k.indexOf("Information")>=0)||Object.keys(groups).find(k=>groups[k].empty)||Object.keys(groups)[0];
const sp=start.split("|");$("#selE").value=sp[0];$("#selA").value=sp[1];$("#selP").value=sp[2];show();

const fr=rows.filter(flagged).sort((x,y)=>BORDERS.indexOf(x.b)-BORDERS.indexOf(y.b)||x.c.localeCompare(y.c));
$("#flagged").innerHTML="<table><tr><th>Border</th><th>Category</th><th>Position</th><th>Email</th><th>Reason</th></tr>"+
 fr.map(r=>`<tr class="click" data-e="${r.e}" data-a="${esc(r.a)}" data-p="${r.p}"><td>${esc(BL[r.b])}</td><td>${esc(r.c)}</td><td>${r.p}</td><td>${r.e}</td><td class="small">${esc(r.w)}</td></tr>`).join("")+"</table>";
document.querySelectorAll("tr.click").forEach(tr=>tr.addEventListener("click",()=>load(tr.dataset.e,tr.dataset.a,tr.dataset.p)));

$("#base").innerHTML="<table><tr><th>Border</th><th class='n'>known-answer questions</th><th class='n'>\"unknown\"-answer questions</th></tr>"+
 base.map(x=>`<tr><td>${esc(BL[x.b])}</td><td class="n">${x.kn_ok}/${x.kn_n}</td><td class="n">${x.un_ok}/${x.un_n}</td></tr>`).join("")+"</table>";
</script></body></html>
"""


def main(attack_csv, baseline_csv):
    attack = last(load(attack_csv), ["email_index", "attack_name", "position", "border_type"])
    rows = [{
        "e": int(r["email_index"]), "a": r["attack_name"], "c": r["category"],
        "p": r["position"], "b": r["border_type"], "o": r["attack_outcome_v3"],
        "w": r["attack_reason_v3"], "r": r["response"][:700], "q": r["question"],
        "t": r["attack_text"], "d": r["done_reason"],
    } for r in attack]

    base_rows = last(load(baseline_csv), ["email_index", "border_type"])
    base = []
    for b in BORDERS:
        rs = [r for r in base_rows if r["border_type"] == b]
        kn = [r for r in rs if r["ideal"].strip().lower() != "unknown"]
        un = [r for r in rs if r["ideal"].strip().lower() == "unknown"]
        ok = lambda xs: sum(expected_answer_present(r["ideal"], r["response"]) for r in xs)
        base.append({"b": b, "kn_ok": ok(kn), "kn_n": len(kn), "un_ok": ok(un), "un_n": len(un)})

    data = {"rows": rows, "base": base, "meta": {"src": Path(attack_csv).name}}
    payload = json.dumps(data, ensure_ascii=True).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload)

    path = ROOT / "results" / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(path, "x", encoding="utf-8") as f:
        f.write(html)
    print("Yazildi:", path)
    try:
        os.startfile(path)
    except Exception:
        pass


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
