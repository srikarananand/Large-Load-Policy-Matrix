# Large-load policy matrix

How do public energy plans treat data centers and other large new loads? This project reads state energy plans and utility resource plans, records what each says across 8 attributes, and refuses to count any claim whose quote is not word for word on the cited page.

**Where this started:** the state energy-plan RAG assistant (RAG Energy Plan Analyzer) from my Research Analyst internship at the Hamm Institute for American Energy at Oklahoma State University (2025). This project extends that work from answering questions to comparing policies, with an evidence guard on every claim.

**Report:** `docs/index.html` (enable GitHub Pages on `/docs`).

## What the published run found

- All 11 documents were read (8 excerpted in a browser, the 3 New York volumes from supplied PDFs).
- 36 claims were made; all 36 quotes were found verbatim in their cited excerpts. The guard initially rejected 2 New York quotes because the PDF text layer spells "New York" as "New Y ork"; the quotes now keep that spelling.
- Only Virginia (state plan) and Dominion Energy Virginia (utility plan) state a dedicated large-load rate class, a financial commitment and a cost-allocation principle. New York states a beneficiary-pays principle and quantifies large-load demand; other documents stop at principle or mention.

## What this does not show

- **Who coded the cells.** The published labels and quotes were written by Claude from the excerpts in a single session (`data/extractions/claude_in_session.py`). The fully automated extractor (`largeload/extract.py`, Groq) is included but was not run for this report.
- **Label accuracy is unmeasured.** The guard proves a quote exists on the page. It cannot tell whether the status label (provision, planned, mentioned) is the right reading; fault injection caught 0% of overstated statuses. `eval/review_sheet.csv` holds a stratified sample of cells for a second reader to mark; `python -m largeload.review score eval/review_sheet.csv` computes precision.
- **Excerpts, not full pages.** The guard checks quotes against text windows around large-load terms. The 8 browser-extracted excerpt files in `data/excerpts/` were transcribed into the repo and each matches a SHA-256 computed in the browser; the 3 `ny_*` files were produced in the sandbox from the supplied PDFs (`excerpt_sha256` in `outputs/results.json`).
- **"Not found" is not "not present."** Maine and Utah returned almost no large-load text.
- The matrix records what documents say, not what is law or tariff in force.

## Reproduce

```bash
pip install -r requirements.txt
python -m pytest -q tests                        # 15 tests, no network
python -m largeload.run_excerpts                 # rebuild outputs/results.json from data/excerpts
python -m largeload.report                       # rebuild docs/index.html
GROQ_API_KEY=... python -m largeload.run         # full automated run: download, retrieve, extract with an LLM, guard
python -m largeload.faults                       # guard fault injection on synthetic documents
```

## Layout

| Path | Purpose |
|---|---|
| `largeload/taxonomy.yaml` | 8 attributes, status points, scores |
| `largeload/sources.yaml` | the 11 public documents |
| `largeload/retrieve.py`, `extract.py` | page retrieval and LLM extraction |
| `largeload/guard.py` | verbatim-quote evidence guard |
| `largeload/aggregate.py` | jurisdiction matrix, scores, KPIs |
| `largeload/faults.py`, `synthetic.py` | fault injection on synthetic text |
| `largeload/run_excerpts.py`, `excerpts.py` | build results from verified excerpt files |
| `.github/workflows/` | scheduled run (needs `GROQ_API_KEY`) and tests |
