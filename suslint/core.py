import importlib
import pkgutil
import yaml
from typing import Iterable
from pathlib import Path
from suslint.rule import Issue, Rule


def load_rules() -> list[Rule]:
    import suslint.rules

    rules: list[Rule] = []

    for mod in pkgutil.iter_modules(suslint.rules.__path__):
        module = importlib.import_module(f"suslint.rules.{mod.name}")

        if hasattr(module, "RULE"):
            rules.append(module.RULE)

    return rules


def lint(path: Path, rules: Iterable[Rule]) -> list[Issue]:
    with open(path) as f:
        workflow = yaml.safe_load(f)

    issues: list[Issue] = []

    for rule in rules:
        issues.extend(rule.check(workflow))

    return issues