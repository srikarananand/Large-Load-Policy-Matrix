"""Read hash-verified excerpt files (data/excerpts/*.txt) and run the evidence guard over supplied cells.

An excerpt file holds, per cited page, the text windows around large-load terms. The guard treats those
windows as the page text, so a quote must be found verbatim inside a window. Windows are joined with a
marker so a quote cannot straddle two windows.
"""
import hashlib
import re
from pathlib import Path

SEP = "\n@@ window\n"


def parse(path):
    """Return (url, meta, {page: text}) from one excerpt file."""
    raw = Path(path).read_text(encoding="utf-8")
    head, _, body = raw.partition("\n@@ page ")
    lines = head.split("\n")
    url = lines[0].removeprefix("### ").strip()
    meta = dict(re.findall(r"(\w+)=([\d,]+)", lines[1])) if len(lines) > 1 else {}
    pages = {}
    if body:
        for blk in ("@@ page " + body).split("@@ page ")[1:]:
            no, _, txt = blk.partition("\n")
            pages[int(no)] = txt.rstrip("\n")
    return url, meta, pages


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
