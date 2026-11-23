"""Render docs/index.html from outputs/results.json and outputs/guard_faults.json (answer-first report)."""
import html
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
TAX = yaml.safe_load((Path(__file__).parent / "taxonomy.yaml").read_text())
esc = html.escape
LABEL = {"explicit_provision": "Provision", "planned_or_recommended": "Planned", "mentioned_only": "Mentioned", "not_addressed": "Not found"}
SHADE = {"explicit_provision": "#1f4e79", "planned_or_recommended": "#6c9bc9", "mentioned_only": "#cfe0f1", "not_addressed": "#f4f4f2"}
INK = {"explicit_provision": "#fff", "planned_or_recommended": "#0b1f33", "mentioned_only": "#0b1f33", "not_addressed": "#6b6b6b"}


def build(res=None, faults=None):
    res = res or json.loads((REPO / "outputs/results.json").read_text())
    faults = faults or json.loads((REPO / "outputs/guard_faults.json").read_text())
    attrs = TAX["attributes"]
    docs = {d["id"]: d for d in res["all_documents"]}
    k = res["kpis"]
    J = res["jurisdictions"]
    n_read, n_all = k["documents_read"], k["documents_total"]
    sc = k["status_counts"]
    top = [j for j in J if j["protection"] == 100.0]
    top_names = " and ".join(j["jurisdiction"] for j in top)
    prov_by_attr = {a["id"]: sum(1 for j in J if j["cells"][a["id"]] and j["cells"][a["id"]]["status"] == "explicit_provision") for a in attrs}
    n_j = len(J)
    hard = [a["name"] for a in attrs if a["id"] in ("dedicated_tariff", "financial_commitment")]

    # ---- Exhibit 1: matrix ----
    head = "".join(f"<th scope='col'>{esc(a['name'])}</th>" for a in attrs)
    rows, ev = [], []
    n = 0
    for j in J:
        tds = []
        for a in attrs:
            c = j["cells"][a["id"]]
            st = c["status"] if c else "not_addressed"
            if c:
                n += 1
                eid = f"e{n}"
                ev.append((eid, j, a, c))
                inner = f"<a href='#{eid}' style='color:inherit'>{LABEL[st]}</a>"
            else:
                inner = LABEL[st]
            tds.append(f"<td style='background:{SHADE[st]};color:{INK[st]}'>{inner}</td>")
        rows.append(f"<tr><th scope='row'>{esc(j['jurisdiction'])}</th>{''.join(tds)}"
                    f"<td class='num'>{j['specificity']:.0f}</td><td class='num'>{j['protection']:.0f}</td></tr>")
    legend = "".join(f"<span class='key' style='background:{SHADE[s]};color:{INK[s]}'>{LABEL[s]}</span>" for s in SHADE)

    # ---- Exhibit 2: evidence ----
    evrows = []
    for eid, j, a, c in ev:
        d = docs[c["doc_id"]]
        link = f"{d['url'].split('#')[0]}#page={c['page']}"
        vals = ", ".join(c["values"]) if c["values"] else ""
        evrows.append(
            f"<tr id='{eid}'><td>{esc(j['jurisdiction'])}</td><td>{esc(a['name'])}</td><td>{LABEL[c['status']]}</td>"
            f"<td>&ldquo;{esc(c['quote'])}&rdquo;{'<br><small>Values: ' + esc(vals) + '</small>' if vals else ''}</td>"
            f"<td><a href='{esc(link)}'>{esc(d['title'])}, p.{c['page']}</a></td></tr>")

    # ---- Exhibit 3: coverage ----
    cov = []
    for s in res["document_status"]:
        d = docs[s["id"]]
        if s["ok"]:
            mine = [c for c in res["cells"] if c["doc_id"] == s["id"] and c["status"] != "not_addressed"]
            cov.append(f"<tr><td>{esc(d['title'])}</td><td>{s['pages']}</td><td>{s['anchor_pages']}</td><td>{len(s['pages_sent'])}</td><td>{len(mine)}</td></tr>")
        else:
            cov.append(f"<tr><td>{esc(d['title'])}</td><td colspan='4'><em>Not read: {esc(s['error'])}</em></td></tr>")

    f = faults
    caught = lambda key: f[key]["caught_pct"]
    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Who protects ratepayers from data-center load? A policy matrix with an evidence guard</title>
<style>
body{{font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;color:#1c1c1c;max-width:1040px;margin:0 auto;padding:28px 18px 80px}}
h1{{font-size:28px;line-height:1.25;margin:0 0 8px}} h2{{font-size:20px;margin:36px 0 8px;border-top:2px solid #1f4e79;padding-top:12px}}
.sub{{color:#555;margin:0 0 18px}} .scr p{{margin:6px 0}} .num{{text-align:right;font-variant-numeric:tabular-nums}}
table{{border-collapse:collapse;width:100%;font-size:14px}} th,td{{border:1px solid #ddd;padding:6px 8px;vertical-align:top;text-align:left}}
thead th{{background:#f0f4f8;font-size:12.5px}} .exh{{font-weight:600;margin:18px 0 4px}} .src{{color:#666;font-size:12.5px;margin:4px 0 0}}
.sowhat{{background:#eef4fa;border-left:4px solid #1f4e79;padding:10px 14px;margin:12px 0}} .key{{display:inline-block;padding:2px 10px;margin:0 6px 4px 0;font-size:12.5px;border:1px solid #ccc}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}} .kpi{{border:1px solid #ddd;padding:10px 12px}}
.kpi b{{display:block;font-size:26px;color:#1f4e79}} small{{color:#555}} .scroll{{overflow-x:auto}} td small{{display:block;margin-top:4px}}
</style></head><body>
<h1>Only {esc(top_names)} put hard cost terms on data centers; the other plans stop at principle or mention</h1>
<p class="sub">Large-load policy matrix across {n_read} public state energy plans and utility resource plans &middot; built {esc(res['generated_at'][:10])}</p>
<p class="sub"><b>Where this started:</b> the state energy-plan RAG assistant from my Research Analyst internship at the Hamm Institute for American Energy at Oklahoma State University (2025), extended from answering questions to comparing policies.</p>

<div class="scr"><h2 style="border:0;padding:0;margin-top:8px">Executive summary</h2>
<p><b>Situation.</b> Data centers are the main driver of new US electricity demand, and regulators are deciding who pays for the grid they need. State plans and utility resource plans are where that stance is written down, but they are long and inconsistent, so they are hard to compare.</p>
<p><b>Complication.</b> Reading them by hand does not scale, and a language model summary is not trustworthy unless every claim can be traced to the page it came from.</p>
<p><b>Resolution.</b> This study codes {n_read} of {n_all} documents against 8 attributes. Every claim carries a quote that an automated guard confirmed appears word for word on the cited page. The result: only {esc(top_names)} score 100 on ratepayer protection, meaning each has a dedicated rate class, a financial commitment and a cost-allocation principle on the page. New York and New Jersey score {next(j['protection'] for j in J if j['jurisdiction']=='New York'):.0f} each, resting on a cost-allocation principle alone, and Maine, Oregon and Utah score 0 on the pages retrieved.</p></div>

<div class="kpis">
<div class="kpi"><b>{n_read} of {n_all}</b>documents read</div>
<div class="kpi"><b>{k['claimed_cells']}</b>claims made, {k['verified_cells']} pass the quote check</div>
<div class="kpi"><b>{sc.get('explicit_provision',0)}</b>explicit provisions</div>
<div class="kpi"><b>{prov_by_attr['dedicated_tariff']} of {n_j}</b>jurisdictions with a dedicated large-load rate class</div>
</div>

<h2>1. The matrix: hard terms appear in Virginia and Dominion, nowhere else</h2>
<p class="exh">Exhibit 1: What each document says about large new loads</p>
<p>{legend}</p>
<div class="scroll"><table><thead><tr><th>Jurisdiction</th>{head}<th>Specificity</th><th>Protection</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="src">Source: public documents listed in Exhibit 3; coded by Claude from hash-verified excerpts and checked by the evidence guard. Specificity is the share of the 16 available points across 8 attributes (provision = 2, planned = 1, mention = 0). Protection uses cost allocation, dedicated tariff and financial commitment. Click a cell to see its quote.</p>
<div class="sowhat"><b>So what.</b> Virginia's SCC-created large-load class (14-year term, minimum demand charges, collateral, exit fees) and Dominion's deposit and three-contract structure are the only places a financial commitment is stated as a rule. For a planner or analyst, this is the template to compare other states against, and the gap to ask about elsewhere.</div>

<h2>2. Evidence: every cell links to its quote and page</h2>
<p class="exh">Exhibit 2: Verified evidence behind each non-empty cell</p>
<div class="scroll"><table><thead><tr><th>Jurisdiction</th><th>Attribute</th><th>Status</th><th>Quote</th><th>Source page</th></tr></thead><tbody>{''.join(evrows)}</tbody></table></div>
<p class="src">Source: same documents. Page links use the PDF page number, which can differ from the printed page number.</p>

<h2>3. Coverage: what was and was not read</h2>
<p class="exh">Exhibit 3: Documents, pages and claims</p>
<div class="scroll"><table><thead><tr><th>Document</th><th>Pages</th><th>Pages mentioning large loads</th><th>Pages excerpted</th><th>Claims</th></tr></thead><tbody>{''.join(cov)}</tbody></table></div>
<p class="src">Source: pipeline run log. &ldquo;Not found&rdquo; means not found in the excerpted pages, which is weaker than not present in the document.</p>
<div class="sowhat"><b>So what.</b> New York's plan sets a &ldquo;beneficiary pays&rdquo; principle and quantifies large-load demand, but the excerpts show no dedicated rate class or financial commitment. Treat that as &ldquo;not found in the excerpted pages&rdquo;, not as proof that neither exists.</div>

<h2>4. How far to trust the guard</h2>
<p class="exh">Exhibit 4: Guard fault-injection results (synthetic documents)</p>
<table><thead><tr><th>Test</th><th>Result</th></tr></thead><tbody>
<tr><td>Invented quote rejected</td><td class="num">{caught('fabricated'):.0f}% of {f['fabricated']['n']}</td></tr>
<tr><td>Quote moved to the wrong page rejected</td><td class="num">{caught('wrong_page'):.0f}% of {f['wrong_page']['n']}</td></tr>
<tr><td>Paraphrase presented as a quote rejected</td><td class="num">{caught('paraphrased'):.0f}% of {f['paraphrased']['n']}</td></tr>
<tr><td>Off-topic quote rejected</td><td class="num">{caught('off_topic'):.0f}% of {f['off_topic']['n']}</td></tr>
<tr><td>Altered number rejected</td><td class="num">{caught('altered_number'):.0f}% of {f['altered_number']['n']}</td></tr>
<tr><td>Real quote with PDF noise still accepted</td><td class="num">{f['control_noise']['pass_rate_pct']:.0f}% of {f['control_noise']['n']}</td></tr>
<tr><td><b>Overstated status (e.g. a mention coded as a provision)</b></td><td class="num"><b>{caught('status_inflated'):.0f}% of {f['status_inflated']['n']} caught</b></td></tr>
</tbody></table>
<p class="src">Source: largeload.faults on synthetic documents. These tests measure the guard, not the accuracy of the coding on real documents.</p>
<div class="sowhat"><b>So what.</b> The guard proves a quote is real and on the cited page. It cannot prove the status label is the right reading. A verified rate of {k['verified_rate_pct']:.0f}% therefore means the evidence exists, not that the coding is correct. Coding accuracy has not been measured.</div>

<h2>5. Limits you should know</h2>
<ul>
<li><b>Coder.</b> The status labels and quotes were written by Claude reading the excerpts in one session. The repository also ships a Groq-based extractor (<code>largeload/extract.py</code>) for a fully automated run; it was not run for this report.</li>
<li><b>Excerpts, not full pages.</b> The guard checks quotes against text windows around large-load terms, not whole pages. The retrieval in the browser step is close to, but not identical with, the Python retrieval in the repo.</li>
<li><b>Provenance.</b> The three New York volumes were supplied as PDF files and excerpted with the repo's Python retrieval; the other eight were excerpted in a browser with pdf.js and hash-checked after transcription. Text layers differ (the New York PDF spells &ldquo;New York&rdquo; as &ldquo;New Y ork&rdquo;, and one quote keeps that spelling so it matches the page).</li>
<li><b>Coverage.</b> Maine and Utah returned almost no large-load text, so their zeros mean &ldquo;nothing retrieved&rdquo;. One PacifiCorp excerpt was cut off before the relevant sentence, so that cell is left empty.</li>
<li><b>Meaning.</b> The matrix records what a document says, not what is law or tariff in force. Utility plans and state plans are different kinds of document and are shown as separate rows.</li>
<li><b>Sample.</b> {n_read} documents is a demonstration, not a survey of US policy.</li>
</ul>

<h2>6. Recommendations and next steps</h2>
<table><thead><tr><th>Action</th><th>Owner</th><th>When</th></tr></thead><tbody>
<tr><td>Run the Groq extractor on the same excerpts and compare its labels with these; report agreement</td><td>Analyst</td><td>Next session</td></tr>
<tr><td>Have a second reader mark the sampled cells in <code>eval/review_sheet.csv</code> to measure label accuracy</td><td>Analyst + reviewer</td><td>Within a week</td></tr>
<tr><td>Add retrieved-page counts so &ldquo;Not found&rdquo; can be split into &ldquo;not present&rdquo; and &ldquo;not retrieved&rdquo;</td><td>Analyst</td><td>Next release</td></tr>
</tbody></table>
</body></html>"""
    return html_doc


def main():
    out = REPO / "docs"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(build(), encoding="utf-8")
    print("wrote docs/index.html")


if __name__ == "__main__":
    main()
