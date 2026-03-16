import importlib
import pkgutil
from pathlib import Path
from typing import Iterable

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

from suslint.rule import Issue, Rule


class LintError(Exception):
    pass


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
    try:
        with open(path, encoding="utf-8") as f:
            workflow = yaml.load(f)
    except YAMLError as exc:
        raise LintError(f"failed to parse YAML: {exc}") from exc

    if not isinstance(workflow, CommentedMap):
        raise LintError("workflow file must contain a mapping at the top level")

    issues: list[Issue] = []

    for rule in rules:
        issues.extend(rule.check(workflow))

    return issues



def lint_file(path: Path, rules: Iterable[Rule]) -> int:
    try:
        issues = lint(path, rules)
    except LintError as exc:
        print(f"{path}:")
        print(f"  error: {exc}")
        return 1

    if not issues:
        return 0

    print(f"{path}:")

    for issue in issues:
        if issue.location:
            print(f"  {issue.rule_id} {issue.location.trail} (line {issue.location.line}, col {issue.location.col}): {issue.message}")
        else:
            print(f"  {issue.rule_id}: {issue.message}")

    return 1
