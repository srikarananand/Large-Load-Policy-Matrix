"""Roll cells up to jurisdictions and compute scores and run KPIs."""
from collections import Counter, defaultdict


def _points(status, taxonomy):
    return taxonomy["statuses"].get(status, {}).get("points", 0)


def jurisdiction_matrix(docs, cells, taxonomy):
    """Per jurisdiction and attribute: the strongest VERIFIED cell across its documents (newest wins ties)."""
    pub = {d["id"]: str(d["published"]) for d in docs}
    best = {}
    for c in cells:
        if not c["verified"] or c["status"] == "not_addressed":
            continue
        key = (c["jurisdiction"], c["attribute"])
        rank = (_points(c["status"], taxonomy), c["status"] == "mentioned_only", pub.get(c["doc_id"], ""))
        # prefer higher points; among equals prefer newest document
        if key not in best or (rank[0], rank[2]) > (best[key][0][0], best[key][0][2]):
            best[key] = (rank, c)
    return {k: v[1] for k, v in best.items()}


def scores(docs, cells, taxonomy):
    attrs = [a["id"] for a in taxonomy["attributes"]]
    prot = taxonomy["scores"]["protection"]["attributes"]
    jm = jurisdiction_matrix(docs, cells, taxonomy)
    juris = sorted({d["jurisdiction"] for d in docs})
    out = []
    for j in juris:
        def idx(subset):
            tot = sum(_points(jm[(j, a)]["status"], taxonomy) for a in subset if (j, a) in jm)
            return round(100.0 * tot / (2 * len(subset)), 1)
        out.append({"jurisdiction": j, "specificity": idx(attrs), "protection": idx(prot),
                    "cells": {a: ({"status": jm[(j, a)]["status"], "doc_id": jm[(j, a)]["doc_id"],
                                   "page": jm[(j, a)]["page"], "quote": jm[(j, a)]["quote"],
                                   "values": jm[(j, a)]["values"]} if (j, a) in jm else None) for a in attrs}})
    out.sort(key=lambda r: (-r["specificity"], r["jurisdiction"]))
    return out


def kpis(docs_status, cells):
    claimed = [c for c in cells if c["status"] not in ("not_addressed", "unparsed", "")]
    ver = [c for c in claimed if c["verified"]]
    reasons = Counter(r for c in claimed if not c["verified"] for r in c["reasons"])
    return {
        "documents_total": len(docs_status),
        "documents_read": sum(1 for d in docs_status if d["ok"]),
        "documents_failed": [d["id"] for d in docs_status if not d["ok"]],
        "cells_total": len(cells),
        "claimed_cells": len(claimed),
        "verified_cells": len(ver),
        "verified_rate_pct": round(100.0 * len(ver) / len(claimed), 1) if claimed else None,
        "not_addressed_cells": sum(1 for c in cells if c["status"] == "not_addressed"),
        "unparsed_cells": sum(1 for c in cells if c["status"] == "unparsed"),
        "status_counts": dict(Counter(c["status"] for c in cells if c["verified"])),
        "rejection_reasons": dict(reasons),
    }
