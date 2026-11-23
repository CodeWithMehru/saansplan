"""Grounded knowledge-base retriever with relevance thresholding."""

import json
import re
from pathlib import Path
from typing import Any

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


class KnowledgeBase:
    """Retrieve grounded KB entries with strict relevance thresholding."""

    def __init__(self, path: str = "app/kb/knowledge.json") -> None:
        self.entries: list[dict[str, Any]] = json.loads(Path(path).read_text(encoding="utf-8"))

    def retrieve(self, question: str, limit: int = 2, threshold: int = 3) -> list[dict[str, Any]]:
        """Return keyword-ranked entries meeting relevance threshold."""
        text = question.lower()
        words = {
            w
            for w in re.findall(r"[A-Za-z0-9]+", text)
            if len(w) >= MIN_WORD_LEN and w not in STOP_WORDS
        }

        ranked: list[tuple[int, dict[str, Any]]] = []
        for entry in self.entries:
            eid = entry["id"]
            topic = entry["topic"].lower()
            haystack = f"{topic} {entry['text']}".lower()

            score = sum(TOPIC_MATCH_WEIGHT if w in topic else 1 for w in words if w in haystack)

            boost_keys = TOPIC_KEYWORDS.get(eid, ())
            if any(k in text for k in boost_keys):
                score += DEFAULT_MATCH_BOOST

            ranked.append((score, entry))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [entry for score, entry in ranked[:limit] if score >= threshold]
