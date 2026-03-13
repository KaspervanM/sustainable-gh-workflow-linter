import importlib
import pkgutil
from ruamel.yaml import YAML
from typing import Iterable
from pathlib import Path
from suslint.rule import Issue, Rule
from suslint.position import pos


def load_rules() -> list[Rule]:
    import suslint.rules

    rules: list[Rule] = []

    for mod in pkgutil.iter_modules(suslint.rules.__path__):
        module = importlib.import_module(f"suslint.rules.{mod.name}")

        if hasattr(module, "RULE"):
            rules.append(module.RULE)

    return rules


def lint(path: Path, rules: Iterable[Rule]) -> list[Issue]:
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(path) as f:
        workflow = yaml.load(f)

    issues: list[Issue] = []

    for rule in rules:
        issues.extend(rule.check(workflow))

    return issues



def lint_file(path: Path, rules: Iterable[Rule]) -> int:
    issues = lint(path, rules)

    if not issues:
        return 0

    print(f"{path}:")

    for issue in issues:
        if issue.location:
            print(f"  {issue.rule_id} {issue.location}: {issue.message}")
        else:
            print(f"  {issue.rule_id}: {issue.message}")

    return 1