"""Human review: sample extracted cells, let a person mark them, and score precision.

The guard proves a quote exists; it cannot prove the status is the right reading. This closes that gap.
    python -m largeload.review make  outputs/results.json eval/review_sheet.csv --n 60
    python -m largeload.review score eval/review_sheet.csv
"""
import csv
import json
import math
import random
import sys

COLS = ["doc_id", "jurisdiction", "attribute", "status", "page", "quote", "link", "reviewer_status_correct", "reviewer_note"]


def make_sheet(results, path, n=60, seed=1):
    docs = {d["id"]: d for d in results["documents"]}
    rows = [c for c in results["cells"] if c["verified"] and c["status"] not in ("not_addressed", "unparsed")]
    rng = random.Random(seed)
    by = {}
    for c in rows:
        by.setdefault(c["status"], []).append(c)
    pick = []
    per = max(1, n // max(1, len(by)))                   # stratify by status so rare statuses are reviewed too
    for st in sorted(by):
        pick += rng.sample(by[st], min(per, len(by[st])))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        for c in pick:
            w.writerow({"doc_id": c["doc_id"], "jurisdiction": c["jurisdiction"], "attribute": c["attribute"],
                        "status": c["status"], "page": c["page"], "quote": c["quote"],
                        "link": f"{docs[c['doc_id']]['url'].split('#')[0]}#page={c['page']}",
                        "reviewer_status_correct": "", "reviewer_note": ""})
    return len(pick)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def score_sheet(path):
    rows = [r for r in csv.DictReader(open(path)) if r["reviewer_status_correct"].strip().lower() in ("yes", "no")]
    k = sum(r["reviewer_status_correct"].strip().lower() == "yes" for r in rows)
    lo, hi = wilson(k, len(rows))
    by = {}
    for r in rows:
        s = by.setdefault(r["status"], [0, 0])
        s[1] += 1
        s[0] += r["reviewer_status_correct"].strip().lower() == "yes"
    return {"reviewed": len(rows), "correct": k, "precision_pct": round(100 * k / len(rows), 1) if rows else None,
            "ci95": [lo, hi], "by_status": {s: {"correct": v[0], "n": v[1]} for s, v in sorted(by.items())}}


if __name__ == "__main__":
    if sys.argv[1] == "make":
        n = make_sheet(json.load(open(sys.argv[2])), sys.argv[3], int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 60)
        print(f"wrote {n} rows to {sys.argv[3]}; fill reviewer_status_correct with yes/no")
    else:
        print(json.dumps(score_sheet(sys.argv[2]), indent=1))
