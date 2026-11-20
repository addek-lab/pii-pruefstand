"""Gemeinsame Datentypen."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    label: str

    def length(self) -> int:
        return self.end - self.start


@dataclass
class Doc:
    id: int
    kind: str                      # z. B. "arztbrief", "ueberweisung"
    text: str
    spans: list = field(default_factory=list)   # Gold-Annotationen (Liste von Span)

    def to_json(self):
        return {"id": self.id, "kind": self.kind, "text": self.text,
                "spans": [[s.start, s.end, s.label] for s in self.spans]}
