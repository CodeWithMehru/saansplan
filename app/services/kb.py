"""Small pure-Python grounded knowledge-base retriever."""

import json
from pathlib import Path
from typing import Any


class KnowledgeBase:
    """Retrieve up to three keyword-matched KB entries."""

    def __init__(self, path: str = "app/kb/knowledge.json") -> None:
        self.entries: list[dict[str, Any]] = json.loads(Path(path).read_text(encoding="utf-8"))

    def retrieve(self, question: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return simple keyword-ranked entries; no network or model call."""
        minimum_word_length = 3
        words = {word.lower() for word in question.split() if len(word) >= minimum_word_length}
        ranked: list[tuple[int, dict[str, Any]]] = []
        for entry in self.entries:
            haystack = f"{entry['topic']} {entry['text']}".lower()
            score = sum(1 for word in words if word in haystack)
            ranked.append((score, entry))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [entry for score, entry in ranked[:limit] if score > 0]
