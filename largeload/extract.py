"""LLM extraction of the policy matrix from retrieved excerpts, one call per document."""
import json
import re
import time

import requests

SYSTEM = (
    "You are a careful policy analyst. You read excerpts of an official energy document and record what it says "
    "about large new electricity loads such as data centers. Use ONLY the excerpts. Never use outside knowledge. "
    "For every attribute return a status and, unless the status is not_addressed, a verbatim quote copied exactly "
    "from one excerpt (at most 60 words) and that excerpt's page number. If no excerpt supports a provision, "
    "return not_addressed with a null quote. Prefer a lower status over a stretched reading. Return JSON only."
)


def build_prompt(doc, excerpts, taxonomy):
    st = "\n".join(f"- {k}: {v['meaning']}" for k, v in taxonomy["statuses"].items())
    at = "\n".join(f"- {a['id']}: {a['question']}" for a in taxonomy["attributes"])
    ex = "\n\n".join(f"[page {p}]\n" + "\n...\n".join(w) for p, w in excerpts.items())
    return (
        f"Document: {doc['title']} ({doc['jurisdiction']}, {doc['published']})\n\n"
        f"Statuses:\n{st}\n\nAttributes:\n{at}\n\n"
        'Return JSON: {"cells":[{"attribute":"<id>","status":"<status>","quote":"<verbatim or null>",'
        '"page":<int or null>,"values":["<numbers with units that appear in the quote>"],"note":"<one short line>"}]} '
        "with exactly one cell per attribute.\n\nExcerpts:\n" + ex
    )


class GroqClient:
    """Groq's OpenAI-compatible chat endpoint. Not exercised offline; see tests for the mocked path."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key, model="openai/gpt-oss-120b", fallback="openai/gpt-oss-20b",
                 min_interval=40.0, session=None, sleep=time.sleep):
        self.key, self.model, self.fallback = api_key, model, fallback
        self.min_interval, self.http, self.sleep = min_interval, session or requests, sleep
        self._last = 0.0
        self.name = model

    def _call(self, model, system, user):
        body = {"model": model, "temperature": 0, "reasoning_effort": "low",
                "response_format": {"type": "json_object"}, "max_completion_tokens": 3000,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        for attempt in range(5):
            wait = self.min_interval - (time.time() - self._last)
            if wait > 0:
                self.sleep(wait)
            r = self.http.post(self.url, headers={"Authorization": f"Bearer {self.key}"}, json=body, timeout=180)
            self._last = time.time()
            if r.status_code == 429 or r.status_code >= 500:
                self.sleep(min(90, float(r.headers.get("retry-after", 20 * (attempt + 1)))))
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        raise RuntimeError(f"{model}: too many retries")

    def complete(self, system, user):
        try:
            return self._call(self.model, system, user)
        except Exception:
            if not self.fallback:
                raise
            self.name = self.fallback
            return self._call(self.fallback, system, user)


def parse_cells(text, taxonomy):
    """Parse model output into one cell per attribute; anything malformed becomes an explicit 'unparsed' cell."""
    ids = [a["id"] for a in taxonomy["attributes"]]
    try:
        m = re.search(r"\{.*\}", text, re.S)
        data = json.loads(m.group(0)) if m else {}
        raw = data.get("cells", []) if isinstance(data, dict) else []
    except Exception:
        raw = []
    by = {c.get("attribute"): c for c in raw if isinstance(c, dict)}
    out = []
    for i in ids:
        c = by.get(i)
        if not c:
            out.append({"attribute": i, "status": "unparsed", "quote": None, "page": None, "values": [], "note": "missing from model output"})
            continue
        try:
            page = int(c["page"]) if c.get("page") is not None else None
        except (TypeError, ValueError):
            page = None
        vals = c.get("values") or []
        out.append({"attribute": i, "status": str(c.get("status", "")).strip(),
                    "quote": (c.get("quote") or None), "page": page,
                    "values": [str(v) for v in vals] if isinstance(vals, list) else [], "note": str(c.get("note") or "")[:200]})
    return out
