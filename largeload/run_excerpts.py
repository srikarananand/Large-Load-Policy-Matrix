"""Build outputs/results.json from hash-verified excerpt files and a cells file (no network, no LLM call).

    python -m largeload.run_excerpts

Extractor of record for the published run: data/extractions/ai_assisted_session.py (cells written by
an AI assistant from the excerpts). Documents without an excerpt file are reported as not read, not scored.
"""
import datetime
import importlib.util
import json
from pathlib import Path

import yaml

from . import aggregate, docs as D, excerpts, guard

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
TAXONOMY = yaml.safe_load((ROOT / "taxonomy.yaml").read_text())
FILES = {"nj-2024-emp": "nj", "me-2025-energy-plan": "me", "va-2026-energy-plan": "va",
         "or-2025-energy-strategy": "or", "ut-energy-innovation-plan-summary": "ut",
         "pacificorp-2025-irp-vol1": "pacificorp", "dominion-2026-irp-update": "dom2026",
         "dominion-2025-irp-update": "dom2025",
         "ny-2025-sep-summary": "ny_summary", "ny-2025-sep-electricity": "ny_electricity",
         "ny-2025-sep-pathways": "ny_pathways"}
UNREACHABLE = "No excerpt file"


def load_cells(path):
    spec = importlib.util.spec_from_file_location("cells_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CELLS


def build(excerpt_dir=REPO / "data/excerpts", cells_path=REPO / "data/extractions/ai_assisted_session.py"):
    cells_by_doc = load_cells(cells_path)
    sources = D.load_sources()
    read, status, all_cells, hashes = [], [], [], {}
    for doc in sources:
        stem = FILES.get(doc["id"])
        f = Path(excerpt_dir) / f"{stem}.txt" if stem else None
        if not f or not f.exists():
            status.append({"id": doc["id"], "ok": False, "error": UNREACHABLE})
            continue
        url, meta, pages = excerpts.parse(f)
        hashes[doc["id"]] = excerpts.sha256(f)
        read.append(doc)
        status.append({"id": doc["id"], "ok": True, "pages": int(meta.get("n_pages", 0)),
                       "pages_sent": sorted(pages), "anchor_pages": int(meta.get("anchor_pages", 0))})
        for cell in cells_by_doc[doc["id"]]:
            ok, why = guard.verify_cell(cell, pages, set(pages), TAXONOMY)
            all_cells.append({**cell, "doc_id": doc["id"], "jurisdiction": doc["jurisdiction"],
                              "verified": ok, "reasons": why})
    return {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "extractor": "An AI assistant, in one session, from hash-verified excerpts (not the Groq pipeline)",
            "documents": read, "all_documents": sources, "document_status": status, "excerpt_sha256": hashes,
            "cells": all_cells, "jurisdictions": aggregate.scores(read, all_cells, TAXONOMY),
            "kpis": aggregate.kpis(status, all_cells)}


def main():
    res = build()
    out = REPO / "outputs"
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res["kpis"], indent=1))
    for j in res["jurisdictions"]:
        print(f"{j['jurisdiction']:<26} specificity {j['specificity']:>5}  protection {j['protection']:>5}")


if __name__ == "__main__":
    main()
