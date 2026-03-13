from dataclasses import dataclass
from typing import Protocol, Iterable


@dataclass
class Issue:
    rule_id: str
    message: str
    location: str | None = None


class Rule(Protocol):
    id: str
    description: str

    def check(self, workflow: dict[str, object]) -> Iterable[Issue]: ...
