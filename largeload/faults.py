"""Fault injection: how often does the evidence guard reject bad evidence, and keep good evidence?

Runs on SYNTHETIC documents only (largeload.synthetic). The result measures the guard, not the
extraction quality on real documents.
"""
import json
import random
import re
from pathlib import Path

import yaml

from . import guard, retrieve, synthetic
from .text import tokens

TAX = yaml.safe_load((Path(__file__).parent / "taxonomy.yaml").read_text())


def _noise(q, rng):
    """PDF-like damage that must NOT cause rejection."""
    q = q.replace("'", "’").replace(" - ", " – ")
    q = re.sub(r" ", lambda m: "  " if rng.random() < 0.15 else " ", q)
    if rng.random() < 0.5:
        q = q.upper() if rng.random() < 0.2 else q
    words = q.split(" ")
    for i, w in enumerate(words):                      # one hyphenated line break inside a long word
        if len(w) > 9 and w.isalpha():
            words[i] = w[:5] + "-\n" + w[5:]
            break
    return " ".join(words)


def make_variants(cell, pages, supplied, rng):
    q, pg = cell["quote"], cell["page"]
    others = [p for p in supplied if p != pg]
    v = {}
    v["fabricated"] = {**cell, "quote": "Large loads shall be required to fund all grid upgrades and post a bond of three years of revenue."}
    if others:
        v["wrong_page"] = {**cell, "page": rng.choice(others)}
    nums = re.findall(r"\d+", q)
    if nums:
        n = nums[0]
        alt = str(int(n) + 7)
        v["altered_number"] = {**cell, "quote": q.replace(n, alt, 1), "values": [alt]}
    w = q.split()
    if len(w) > 6:
        v["paraphrased"] = {**cell, "quote": " ".join(w[:2] + ["generally"] + w[2:])}
    filler = [s for s in synthetic.FILLER]
    v["off_topic"] = {**cell, "quote": rng.choice(filler)}
    if cell["status"] != "explicit_provision":      # true quote, overstated reading: beyond what a string check can see
        v["status_inflated"] = {**cell, "status": "explicit_provision"}
    v["control_noise"] = {**cell, "quote": _noise(q, rng)}
    v["control_exact"] = dict(cell)
    return v


def run(n_docs=40, seed=7):
    rng = random.Random(seed)
    tally = {}
    for d in range(n_docs):
        pages, truth = synthetic.build_doc(seed * 1000 + d)
        text = dict(pages)
        per, union = retrieve.pick_pages(pages, TAX)
        for attr, t in truth.items():
            cell = {"attribute": attr, "status": t["status"], "quote": t["quote"], "page": t["page"], "values": []}
            for name, c in make_variants(cell, text, set(union) | {t["page"]}, rng).items():
                ok, _ = guard.verify_cell(c, text, set(union) | {t["page"]}, TAX)
                s = tally.setdefault(name, {"n": 0, "accepted": 0})
                s["n"] += 1
                s["accepted"] += ok
    out = {}
    for k, s in tally.items():
        if k.startswith("control"):
            out[k] = {"n": s["n"], "pass_rate_pct": round(100.0 * s["accepted"] / s["n"], 1)}
        else:
            out[k] = {"n": s["n"], "caught_pct": round(100.0 * (s["n"] - s["accepted"]) / s["n"], 1)}
    return out


if __name__ == "__main__":
    res = run()
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/guard_faults.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
