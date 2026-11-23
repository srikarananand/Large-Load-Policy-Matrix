"""Evidence guard. A cell counts only if its quote can be found, word for word, on the cited page.

It cannot judge whether the status is the right reading of the quote; that needs human review
(see review.py). What it removes is invented, misplaced, altered and off-topic evidence.
"""
from .text import contains_sequence, has_term, numbers, tokens

MAX_QUOTE_WORDS = 80


def verify_cell(cell, pages, supplied, taxonomy):
    """Return (verified: bool, reasons: list[str]). `pages` = {no: full text}; `supplied` = page numbers sent to the model."""
    statuses = taxonomy["statuses"]
    reasons = []
    st = cell.get("status")
    if st not in statuses:
        return False, ["invalid_status"]
    if st == "not_addressed":
        return True, []                       # absence cannot be proven; reported separately as unchecked
    q, pg = cell.get("quote"), cell.get("page")
    if not q or not str(q).strip():
        return False, ["missing_quote"]
    qt = tokens(q)
    if len(qt) > MAX_QUOTE_WORDS:
        reasons.append("quote_too_long")
    if pg not in supplied:
        reasons.append("page_not_supplied")
    elif not contains_sequence(tokens(pages.get(pg, "")), qt):
        reasons.append("quote_not_on_cited_page")
    qnums = numbers(q)
    for v in cell.get("values", []):
        if not numbers(v) <= qnums:
            reasons.append("value_not_in_quote")
            break
    if not any(has_term(qt, a) for a in taxonomy["anchor_terms"]):
        reasons.append("quote_not_about_large_loads")
    return (not reasons), reasons
