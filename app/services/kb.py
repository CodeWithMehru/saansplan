"""Grounded knowledge-base retriever with relevance thresholding."""

import json
import re
from pathlib import Path
from typing import TypedDict, cast


class KBSource(TypedDict):
    """Citation source metadata."""

    name: str
    url: str
    checked: str


class KBEntry(TypedDict):
    """Knowledge base grounded snippet entry."""

    id: str
    topic: str
    text: str
    source: KBSource


MIN_WORD_LEN = 3
DEFAULT_MATCH_BOOST = 5
TOPIC_MATCH_WEIGHT = 2

STOP_WORDS = {
    "what",
    "size",
    "is",
    "it",
    "to",
    "at",
    "for",
    "the",
    "and",
    "are",
    "can",
    "with",
    "from",
    "how",
    "should",
    "you",
    "this",
    "that",
    "in",
    "a",
    "an",
    "of",
    "on",
    "my",
    "me",
    "i",
    "do",
    "does",
    "have",
    "kya",
    "hai",
    "ke",
    "ko",
    "se",
    "mein",
    "par",
}

TOPIC_KEYWORDS = {
    "purifier-sizing": ("purifier", "cadr", "bedroom", "cleaner", "room", "sq ft", "sqft"),
    "cpcb-aqi-breakpoints": ("walk", "safe", "exercise", "run", "outside", "outdoor"),
    "inhalation-factors": ("walk", "exercise", "run", "breathe", "heavy"),
    "mask-fit": ("mask", "n95", "respirator", "mask-fit"),
    "box-fan-safety": ("box fan", "diy", "merv"),
    "wet-mop": ("mop", "sweep", "dust"),
    "cleaner-cooking": ("chulha", "cooking", "smoke", "kitchen", "lpg"),
    "cooking-vent": ("cooking", "ventilation", "exhaust"),
    "transit-emissions": ("metro", "bus", "car", "transit", "commute"),
    "incense-avoidance": ("incense", "agarbatti", "dhoop"),
}


def _extract_query_words(text: str) -> set[str]:
    """Tokenize query into non-stopword alphanumeric keywords."""
    return {
        w
        for w in re.findall(r"[A-Za-z0-9]+", text.lower())
        if len(w) >= MIN_WORD_LEN and w not in STOP_WORDS
    }


def _word_match_score(word: str, topic: str, haystack: str) -> int:
    """Calculate match score for an individual keyword in entry topic or text."""
    if word not in haystack:
        return 0
    return TOPIC_MATCH_WEIGHT if word in topic else 1


def _score_entry(entry: KBEntry, words: set[str], text: str) -> int:
    """Calculate keyword and domain boost score for a single KB entry."""
    topic = entry["topic"].lower()
    haystack = f"{topic} {entry['text']}".lower()
    score = sum(_word_match_score(w, topic, haystack) for w in words)
    boost_keys = TOPIC_KEYWORDS.get(entry["id"], ())
    has_boost = any(k in text for k in boost_keys)
    return score + (DEFAULT_MATCH_BOOST if has_boost else 0)


class KnowledgeBase:
    """Retrieve grounded KB entries with strict relevance thresholding."""

    def __init__(self, path: str = "app/kb/knowledge.json") -> None:
        """Load knowledge base records from designated JSON storage file."""
        self.entries: list[KBEntry] = cast(
            list[KBEntry], json.loads(Path(path).read_text(encoding="utf-8"))
        )

    def retrieve(self, question: str, limit: int = 2, threshold: int = 3) -> list[KBEntry]:
        """Return keyword-ranked entries meeting relevance threshold."""
        text = question.lower()
        words = _extract_query_words(text)
        ranked = [(_score_entry(entry, words, text), entry) for entry in self.entries]
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [entry for score, entry in ranked[:limit] if score >= threshold]
