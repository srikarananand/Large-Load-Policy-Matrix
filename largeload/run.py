"""Run the pipeline: download, read, retrieve, extract, verify, aggregate, write outputs/results.json."""
import argparse
import datetime
import json
import os
from pathlib import Path

import yaml

from . import aggregate, docs as D, extract, guard, retrieve

ROOT = Path(__file__).resolve().parent
TAXONOMY = yaml.safe_load((ROOT / "taxonomy.yaml").read_text())


def process_doc(doc, pages, client, taxonomy=TAXONOMY):
    """Pure pipeline step: pages in, verified cells out. `client` needs .complete(system, user)."""
    per, union = retrieve.pick_pages(pages, taxonomy)
    text = dict(pages)
    excerpts = {p: retrieve.windows(text[p], taxonomy["anchor_terms"]) for p in union}
    if not union:
        raw, cells = "", extract.parse_cells("", taxonomy)
        for c in cells:
            c.update(status="not_addressed", note="no page mentions large loads")
    else:
        raw = client.complete(extract.SYSTEM, extract.build_prompt(doc, excerpts, taxonomy))
        cells = extract.parse_cells(raw, taxonomy)
    out = []
    for c in cells:
        ok, why = guard.verify_cell(c, text, set(union), taxonomy)
        out.append({**c, "doc_id": doc["id"], "jurisdiction": doc["jurisdiction"], "verified": ok, "reasons": why})
    return {"raw": raw, "pages_sent": union, "candidate_pages": per, "n_pages": len(pages), "cells": out}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="all", help="'all' or space-separated document ids")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--cache", default=".cache")
    ap.add_argument("--model", default="openai/gpt-oss-120b")
    a = ap.parse_args(argv)
    sources = D.load_sources()
    chosen = sources if a.docs == "all" else [d for d in sources if d["id"] in a.docs.split()]
    out = Path(a.out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    client = extract.GroqClient(os.environ["GROQ_API_KEY"], model=a.model)
    cells, status = [], []
    for doc in chosen:
        try:
            pdf = D.download(doc["url"], Path(a.cache) / f"{doc['id']}.pdf")
            pages = D.read_pages(pdf)
            res = process_doc(doc, pages, client)
            (out / "raw" / f"{doc['id']}.json").write_text(json.dumps(
                {"pages_sent": res["pages_sent"], "raw": res["raw"]}, indent=1))
            cells += res["cells"]
            status.append({"id": doc["id"], "ok": True, "pages": res["n_pages"], "pages_sent": res["pages_sent"]})
            print(f"{doc['id']}: {res['n_pages']} pages, sent {res['pages_sent']}")
        except Exception as e:  # one bad document must not sink the run
            status.append({"id": doc["id"], "ok": False, "error": f"{type(e).__name__}: {e}"[:300]})
            print(f"{doc['id']}: FAILED {e}")
    result = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "model": client.name, "documents": chosen, "document_status": status, "cells": cells,
              "jurisdictions": aggregate.scores(chosen, cells, TAXONOMY),
              "kpis": aggregate.kpis(status, cells)}
    (out / "results.json").write_text(json.dumps(result, indent=1, default=str))
    print(json.dumps(result["kpis"], indent=1))


if __name__ == "__main__":
    main()
