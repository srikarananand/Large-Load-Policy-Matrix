"""Text normalisation shared by retrieval and the evidence guard."""
import re

_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                      "−": "-", " ": " ", "­": "", "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff",
                      "•": " "})
_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?%?|[a-z]+")


def tokens(text):
    """Lower-case word and number tokens. Hyphens, spacing, quote styles and PDF line breaks all vanish."""
    t = text.translate(_MAP).lower()
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)       # "electri-\ncity" -> "electricity"
    return [_stem(w) for w in _TOKEN.findall(t)]


def _stem(w):
    """Strip a plural 's' ("data centers" == "data center"); numbers and short words are left alone."""
    return w[:-1] if len(w) > 3 and w.isalpha() and w.endswith("s") and not w.endswith("ss") else w


def numbers(text):
    """Numeric values in text, commas removed ('5,500' -> '5500')."""
    return {tok.rstrip("%").replace(",", "") for tok in tokens(text) if tok[0].isdigit()}


def contains_sequence(haystack, needle):
    """True if token list `needle` occurs contiguously inside token list `haystack`."""
    n = len(needle)
    if n == 0 or n > len(haystack):
        return False
    first = needle[0]
    for i in range(len(haystack) - n + 1):
        if haystack[i] == first and haystack[i:i + n] == needle:
            return True
    return False


def has_term(token_list, term):
    return contains_sequence(token_list, tokens(term))
