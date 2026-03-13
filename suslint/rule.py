from dataclasses import dataclass
from ruamel.yaml.comments import CommentedMap
from typing import Protocol, Iterable


@dataclass
class Location:
    trail: str
    line: int
    col: int

@dataclass
class Issue:
    rule_id: str
    message: str
    location: Location | None = None


class Rule(Protocol):
    id: str
    description: str

    def check(self, workflow: CommentedMap) -> Iterable[Issue]: ...
