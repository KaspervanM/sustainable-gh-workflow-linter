import importlib
import json
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

from suslint.rule import Issue, Rule
from suslint.ignore_comments import get_line_ignores


class LintError(Exception):
    pass


@dataclass
class FileResult:
    path: Path
    issues: list[Issue]
    error: str | None = None


def load_rules() -> list[Rule]:
    import suslint.rules

    rules: list[Rule] = []

    for mod in pkgutil.iter_modules(suslint.rules.__path__):
        module = importlib.import_module(f"suslint.rules.{mod.name}")

        if hasattr(module, "RULE"):
            rules.append(module.RULE)

    return sorted(rules, key=lambda rule: rule.id)


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

    line_ignores = get_line_ignores(workflow)

    issues: list[Issue] = []

    for rule in rules:
        potential_issues = rule.check(workflow)
        for potential_issue in potential_issues:
            line = 0
            location = potential_issue.location
            if location:
                line = location.line
            ignores = line_ignores.get(line, [])
            if potential_issue.rule_id not in ignores:
                issues.append(potential_issue)

    return issues


def lint_path(path: Path, rules: Iterable[Rule]) -> FileResult:
    try:
        return FileResult(path=path, issues=lint(path, rules))
    except LintError as exc:
        return FileResult(path=path, issues=[], error=str(exc))


def count_issues(results: Iterable[FileResult]) -> int:
    return sum(len(result.issues) + (1 if result.error else 0) for result in results)


def count_affected_files(results: Iterable[FileResult]) -> int:
    return sum(1 for result in results if result.error or result.issues)


def render_text(results: list[FileResult], rules: dict[str, Rule], quiet: bool = False) -> str:
    lines: list[str] = []

    for result in results:
        if not result.error and not result.issues:
            if not quiet:
                lines.append(f"Success: no issues found in {result.path}")
            continue

        lines.append(f"{result.path}:")

        if result.error:
            lines.append(f"  error: {result.error}")
            continue

        for issue in result.issues:
            rule = rules[issue.rule_id]
            prefix = f"  {issue.rule_id} [{rule.metadata.severity}/{rule.metadata.category}]"

            if issue.location:
                lines.append(
                    f"{prefix} {issue.location.trail} (line {issue.location.line}, col {issue.location.col}): "
                    f"{issue.message} Fix: {rule.metadata.remediation}"
                )
            else:
                lines.append(f"{prefix}: {issue.message} Fix: {rule.metadata.remediation}")

    total_issues = count_issues(results)
    total_files = count_affected_files(results)
    if total_issues:
        issue_noun = "issue" if total_issues == 1 else "issues"
        file_noun = "file" if total_files == 1 else "files"
        lines.append(f"Summary: {total_issues} {issue_noun} across {total_files} {file_noun}.")

    return "\n".join(lines)


def render_json(results: list[FileResult], rules: dict[str, Rule]) -> str:
    payload = {
        "summary": {
            "issues": count_issues(results),
            "files_with_issues": count_affected_files(results),
        },
        "files": [
            {
                "path": str(result.path),
                "error": result.error,
                "issues": [
                    {
                        "rule_id": issue.rule_id,
                        "message": issue.message,
                        "location": None
                        if issue.location is None
                        else {
                            "trail": issue.location.trail,
                            "line": issue.location.line,
                            "col": issue.location.col,
                        },
                        "severity": rules[issue.rule_id].metadata.severity,
                        "category": rules[issue.rule_id].metadata.category,
                        "remediation": rules[issue.rule_id].metadata.remediation,
                    }
                    for issue in result.issues
                ],
            }
            for result in results
        ],
    }
    return json.dumps(payload, indent=2)


def lint_file(path: Path, rules: Iterable[Rule]) -> int:
    result = lint_path(path, rules)

    if not result.error and not result.issues:
        return 0

    print(f"{path}:")

    if result.error:
        print(f"  error: {result.error}")
        return 1

    for issue in result.issues:
        if issue.location:
            print(f"  {issue.rule_id} {issue.location.trail} (line {issue.location.line}, col {issue.location.col}): {issue.message}")
        else:
            print(f"  {issue.rule_id}: {issue.message}")

    return 1
