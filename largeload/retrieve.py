"""Find the pages worth reading: anchor-term gate, then BM25 per attribute, then compact windows."""
import math
from collections import Counter

from .text import has_term, tokens


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.n = len(docs)
        self.avg = (sum(len(d) for d in docs) / self.n) if self.n else 0
        df = Counter(t for d in docs for t in set(d))
        self.idf = {t: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [Counter(d) for d in docs]

    def score(self, query, i):
        tf, dl = self.tf[i], len(self.docs[i])
        s = 0.0
        for t in set(query):
            if t in tf:
                f = tf[t]
                s += self.idf.get(t, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / (self.avg or 1)))
        return s


def anchor_pages(pages, anchors):
    """Pages that mention at least one large-load anchor term."""
    out = {}
    for no, text in pages:
        tk = tokens(text)
        hits = sum(1 for a in anchors if has_term(tk, a))
        if hits:
            out[no] = hits
    return out


def pick_pages(pages, taxonomy, per_attr=2, cap=10):
    """Return ({attribute_id: [page numbers]}, [union of pages, best first])."""
    anchors = taxonomy["anchor_terms"]
    gate = anchor_pages(pages, anchors)
    cand = [(no, text) for no, text in pages if no in gate]
    if not cand:
        return {a["id"]: [] for a in taxonomy["attributes"]}, []
    bm = BM25([tokens(t) for _, t in cand])
    per, rank = {}, Counter()
    for a in taxonomy["attributes"]:
        q = tokens(" ".join(a["terms"]))
        scored = sorted(((bm.score(q, i) + 0.25 * gate[no], no) for i, (no, _) in enumerate(cand)), reverse=True)
        top = [no for s, no in scored[:per_attr] if s > 0]
        per[a["id"]] = top
        for r, no in enumerate(top):
            rank[no] += per_attr - r
    union = [no for no, _ in rank.most_common(cap)]
    return per, union


def windows(text, anchors, radius=600, budget=2000):
    """Compact excerpts of a page around anchor-term mentions (substrings of the page)."""
    low = text.lower()
    spans = []
    for a in anchors:
        start = 0
        key = a.lower()
        while True:
            i = low.find(key, start)
            if i < 0:
                break
            spans.append((max(0, i - radius), min(len(text), i + len(key) + radius)))
            start = i + len(key)
    if not spans:
        return [text[:budget]]
    spans.sort()
    merged = [list(spans[0])]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out, used = [], 0
    for s, e in merged:
        seg = text[s:e]
        if used + len(seg) > budget:
            seg = seg[: max(0, budget - used)]
        if seg:
            out.append(seg)
            used += len(seg)
        if used >= budget:
            break
    return out
