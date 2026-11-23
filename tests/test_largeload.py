import csv
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from largeload import aggregate, extract, faults, guard, retrieve, review, run, synthetic  # noqa: E402
from largeload.text import contains_sequence, numbers, tokens  # noqa: E402

TAX = yaml.safe_load((ROOT / "largeload/taxonomy.yaml").read_text())
DOC = {"id": "syn-1", "jurisdiction": "Exampleland", "title": "Synthetic plan", "published": "2026-01-01", "url": "http://x/y.pdf"}


def oracle(truth):
    """A stand-in for the model that reports the planted truth."""
    class C:
        name = "oracle"
        def complete(self, system, user):
            cells = [{"attribute": a, "status": t["status"], "quote": t["quote"], "page": t["page"], "values": [], "note": ""}
                     for a, t in truth.items()]
            return json.dumps({"cells": cells})
    return C()


def test_tokens_ignore_pdf_noise():
    a = tokens("Large-load customers\n must post collateral of 5,500 MW.")
    b = tokens("large load  customers must post COLLATERAL of 5,500 MW")
    assert a == b
    assert tokens("elec-\ntricity") == tokens("electricity")
    assert tokens("data centers") == tokens("data center")
    assert numbers("5,500 MW and 12.5%") == {"5500", "12.5"}
    assert contains_sequence(tokens("a b c d"), tokens("b c")) and not contains_sequence(tokens("a b c d"), tokens("b d"))


def test_guard_accepts_verbatim_and_rejects_bad_evidence():
    pages = {3: "Large load customers must post collateral of 150 MW equivalent.\nOther text.", 4: "Unrelated page."}
    base = {"attribute": "financial_commitment", "status": "explicit_provision",
            "quote": "Large load customers must post collateral of 150 MW equivalent.", "page": 3, "values": ["150 MW"]}
    ok, _ = guard.verify_cell(base, pages, {3, 4}, TAX)
    assert ok
    for change, reason in [({"quote": "Large load customers must post a bond of 3 years."}, "quote_not_on_cited_page"),
                           ({"page": 4}, "quote_not_on_cited_page"),
                           ({"page": 9}, "page_not_supplied"),
                           ({"values": ["170 MW"]}, "value_not_in_quote"),
                           ({"quote": None}, "missing_quote"),
                           ({"status": "very_explicit"}, "invalid_status")]:
        ok, why = guard.verify_cell({**base, **change}, pages, {3, 4}, TAX)
        assert not ok and reason in why, (change, why)


def test_guard_requires_large_load_topic():
    pages = {1: "The department held workshops in each region."}
    c = {"attribute": "flexibility", "status": "mentioned_only", "quote": "The department held workshops in each region.", "page": 1, "values": []}
    ok, why = guard.verify_cell(c, pages, {1}, TAX)
    assert not ok and "quote_not_about_large_loads" in why


def test_absence_is_not_claimed_as_verified_evidence():
    ok, _ = guard.verify_cell({"status": "not_addressed", "quote": None}, {}, set(), TAX)
    assert ok
    cells = [{"status": "not_addressed", "verified": True}]
    assert aggregate.kpis([{"id": "a", "ok": True}], cells)["claimed_cells"] == 0


def test_pipeline_with_oracle_recovers_planted_provisions():
    pages, truth = synthetic.build_doc(11)
    res = run.process_doc(DOC, pages, oracle(truth))
    got = {c["attribute"]: c for c in res["cells"]}
    for a, t in truth.items():
        assert got[a]["verified"] and got[a]["status"] == t["status"], a
    assert len(res["cells"]) == len(TAX["attributes"])
    assert all(got[a]["status"] == "unparsed" for a in got if a not in truth)


def test_retrieval_puts_planted_pages_in_prompt():
    hit = tot = 0
    for s in range(30):
        pages, truth = synthetic.build_doc(500 + s)
        _, union = retrieve.pick_pages(pages, TAX)
        for t in truth.values():
            tot += 1
            hit += t["page"] in union
    assert hit / tot >= 0.9   # sanity check on synthetic text only; real documents are harder


def test_malformed_model_output_never_becomes_evidence():
    cells = extract.parse_cells("not json at all", TAX)
    assert all(c["status"] == "unparsed" for c in cells)
    res = run.process_doc(DOC, synthetic.build_doc(3)[0], type("C", (), {"complete": lambda s, a, b: "garbage"})())
    assert not any(c["verified"] for c in res["cells"])


def test_doc_without_anchor_pages_is_all_not_addressed():
    class Boom:
        def complete(self, *a): raise AssertionError("no model call should be made")
    res = run.process_doc(DOC, [(1, "Plain text about maintenance."), (2, "More filler.")], Boom())
    assert all(c["status"] == "not_addressed" for c in res["cells"])


def test_scores_use_verified_cells_only():
    docs = [DOC]
    base = {"doc_id": "syn-1", "jurisdiction": "Exampleland", "values": [], "reasons": [], "quote": "q", "page": 1}
    cells = [{**base, "attribute": a["id"], "status": "explicit_provision", "verified": a["id"] != "flexibility"}
             for a in TAX["attributes"]]
    s = aggregate.scores(docs, cells, TAX)[0]
    assert s["specificity"] == round(100 * 14 / 16, 1)   # 7 of 8 verified explicit cells = 14 of 16 points
    assert s["protection"] == 100.0


def test_groq_client_retries_and_falls_back():
    class R:
        def __init__(self, code, body=None): self.status_code, self._b, self.headers = code, body, {"retry-after": "0"}
        def raise_for_status(self):
            if self.status_code >= 400: raise RuntimeError("http")
        def json(self): return {"choices": [{"message": {"content": self._b}}]}
    calls = []
    class H:
        def post(self, url, headers, json, timeout):
            calls.append(json["model"])
            return R(429) if len(calls) == 1 else R(200, '{"cells":[]}')
    c = extract.GroqClient("k", min_interval=0, session=H(), sleep=lambda s: None)
    assert c.complete("s", "u") == '{"cells":[]}' and len(calls) == 2


def test_guard_fault_injection_catches_bad_evidence_and_keeps_good():
    r = faults.run(n_docs=15)
    for k in ("fabricated", "wrong_page", "altered_number", "paraphrased", "off_topic"):
        assert r[k]["caught_pct"] >= 99, (k, r[k])
    assert r["control_noise"]["pass_rate_pct"] >= 99 and r["control_exact"]["pass_rate_pct"] >= 99
    assert r["status_inflated"]["caught_pct"] == 0.0     # documented limit: needs human review


def test_review_sheet_roundtrip(tmp_path):
    pages, truth = synthetic.build_doc(21)
    res = run.process_doc(DOC, pages, oracle(truth))
    results = {"documents": [DOC], "cells": res["cells"]}
    p = tmp_path / "sheet.csv"
    n = review.make_sheet(results, p, n=6)
    rows = list(csv.DictReader(open(p)))
    assert n == len(rows) > 0 and rows[0]["link"].endswith("#page=" + rows[0]["page"])
    for i, r in enumerate(rows):
        r["reviewer_status_correct"] = "yes" if i % 2 == 0 else "no"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)
    s = review.score_sheet(p)
    assert s["reviewed"] == n and s["ci95"][0] <= s["precision_pct"] <= s["ci95"][1]


def test_pdf_reader_extracts_pages(tmp_path):
    rl = pytest.importorskip("reportlab.pdfgen.canvas")
    from largeload import docs
    p = tmp_path / "a.pdf"
    c = rl.Canvas(str(p))
    c.drawString(72, 700, "Large load customers must post collateral.")
    c.showPage(); c.drawString(72, 700, "Second page text."); c.save()
    pages = docs.read_pages(p)
    assert [n for n, _ in pages] == [1, 2] and "collateral" in pages[0][1]


def test_session_excerpts_pass_guard_and_hashes_recorded():
    """The published run: every claimed cell is verbatim in its hash-recorded excerpt; unreachable docs are not scored."""
    from largeload import run_excerpts
    res = run_excerpts.build()
    assert res["kpis"]["documents_read"] == 11 and not res["kpis"]["documents_failed"]
    claimed = [c for c in res["cells"] if c["status"] != "not_addressed"]
    assert claimed and all(c["verified"] for c in claimed)
    assert all(len(h) == 64 for h in res["excerpt_sha256"].values())
    assert "New York" in {j["jurisdiction"] for j in res["jurisdictions"]}


def test_guard_rejects_edited_session_quote():
    from largeload import excerpts, guard, run_excerpts
    _, _, pages = excerpts.parse(run_excerpts.REPO / "data/excerpts/va.txt")
    bad = {"attribute": "dedicated_tariff", "status": "explicit_provision", "page": 42,
           "quote": "The SCC has created a separate large load rate class and a 20-year contract term", "values": []}
    ok, why = guard.verify_cell(bad, pages, set(pages), run_excerpts.TAXONOMY)
    assert not ok and "quote_not_on_cited_page" in why
