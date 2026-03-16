from dataclasses import dataclass
from typing import Iterable, Protocol

from ruamel.yaml.comments import CommentedMap


@dataclass
class Location:
    trail: str
    line: int
    col: int


@dataclass(frozen=True)
class RuleMetadata:
    severity: str
    category: str
    remediation: str


@dataclass
class Issue:
    rule_id: str
    message: str
    location: Location | None = None


class Rule(Protocol):
    id: str
    description: str
    metadata: RuleMetadata

    def check(self, workflow: CommentedMap) -> Iterable[Issue]: ...
