"""Download documents and read them page by page (PyMuPDF if installed, else pypdf)."""
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 "
      "largeload-matrix/1.0")


def load_sources(path=None):
    return yaml.safe_load(Path(path or ROOT / "sources.yaml").read_text())["documents"]


def download(url, dest, timeout=180):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    with requests.get(url, headers={"User-Agent": UA}, timeout=timeout, stream=True) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for block in r.iter_content(1 << 16):
                f.write(block)
    if tmp.read_bytes()[:5] != b"%PDF-":
        tmp.unlink()
        raise ValueError("response was not a PDF")
    tmp.rename(dest)
    return dest


def read_pages(path):
    """[(1-based page number, text)] for pages that have text."""
    try:
        import fitz
        out = []
        with fitz.open(path) as pdf:
            for i, page in enumerate(pdf):
                t = page.get_text("text").strip()
                if t:
                    out.append((i + 1, t))
        return out
    except ImportError:
        from pypdf import PdfReader
        out = []
        for i, page in enumerate(PdfReader(str(path)).pages):
            t = (page.extract_text() or "").strip()
            if t:
                out.append((i + 1, t))
        return out
