"""Private relational symbolism as first-class durable objects."""

from dataclasses import dataclass
from typing import Dict, Optional, List
import re


@dataclass
class SharedSymbol:
    name: str
    meaning: str
    created_at: float
    emotional_charge: float
    last_referenced: float
    stability: float = 0.5


class SymbolStore:
    def __init__(self):
        self.symbols: Dict[str, SharedSymbol] = {}

    def add(self, symbol: SharedSymbol):
        existing = self.symbols.get(symbol.name)
        if existing:
            existing.emotional_charge = min(1.0, max(existing.emotional_charge, symbol.emotional_charge) + 0.05)
            existing.stability = min(1.0, existing.stability + 0.04)
            existing.last_referenced = symbol.last_referenced
        else:
            self.symbols[symbol.name] = symbol

    def detect_from_text(self, text: str, now: float, relationship=None) -> List[SharedSymbol]:
        lowered = text.lower()
        created: List[SharedSymbol] = []
        charge_base = 0.3 + (getattr(relationship, "attachment", 0.0) * 0.3 if relationship else 0.0)
        patterns = [
            (r"call me ([a-zA-Z0-9_ -]{2,32})", "nickname for the user"),
            (r"call you ([a-zA-Z0-9_ -]{2,32})", "nickname for the character"),
            (r"let'?s call (?:this|it|that) ([a-zA-Z0-9_ -]{2,48})", "user-named shared symbol"),
            (r"our symbol is ([a-zA-Z0-9_ -]{2,48})", "declared shared symbol"),
            (r"remember the ([a-zA-Z0-9_ -]{2,48})", "shared reference"),
        ]
        for pattern, meaning in patterns:
            for match in re.finditer(pattern, lowered):
                name = " ".join(match.group(1).split()).strip(" .,!?:;")
                if len(name) >= 2:
                    symbol = SharedSymbol(name=name, meaning=meaning, created_at=now, emotional_charge=min(1.0, charge_base), last_referenced=now, stability=0.35)
                    self.add(symbol)
                    created.append(symbol)
        promise = re.search(r"(i promise|we promise|promise me)(.{1,100})", lowered)
        if promise:
            name = "promise:" + promise.group(2).strip(" .,!?:;")[:40]
            symbol = SharedSymbol(name=name, meaning="shared promise", created_at=now, emotional_charge=0.65, last_referenced=now, stability=0.45)
            self.add(symbol)
            created.append(symbol)
        ritual = re.search(r"(always|every time|whenever)(.{1,100})", lowered)
        if ritual:
            name = "ritual:" + ritual.group(2).strip(" .,!?:;")[:40]
            symbol = SharedSymbol(name=name, meaning="repeated relational ritual", created_at=now, emotional_charge=0.5, last_referenced=now, stability=0.4)
            self.add(symbol)
            created.append(symbol)
        for symbol in self.symbols.values():
            if symbol.name.lower() in lowered:
                symbol.last_referenced = now
                symbol.stability = min(1.0, symbol.stability + 0.02)
        return created

    def lifecycle_tick(self, now: float):
        for symbol in self.symbols.values():
            age = max(0.0, now - symbol.last_referenced)
            if age > 86400:
                symbol.emotional_charge *= 0.95
                symbol.stability *= 0.98

    def most_relevant(self, now: float) -> Optional[SharedSymbol]:
        if not self.symbols:
            return None
        self.lifecycle_tick(now)
        return max(self.symbols.values(), key=lambda s: s.emotional_charge * s.stability)
