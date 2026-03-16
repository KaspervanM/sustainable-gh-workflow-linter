from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

from suslint.core import FileResult, lint_path, load_rules, render_json, render_text
from suslint.rule import Rule


def _split_rule_ids(values: list[str]) -> set[str]:
    result: set[str] = set()

    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                result.add(item)

    return result


def _expand_target(target: str) -> list[Path]:
    if any(char in target for char in "*?[]"):
        return sorted({Path(path).resolve() for path in glob.glob(target, recursive=True)})

    path = Path(target)
    if path.is_dir():
        matches = list(path.rglob("*.yml")) + list(path.rglob("*.yaml"))
        return sorted({match.resolve() for match in matches if match.is_file()})

    if path.exists():
        return [path.resolve()]

    return []


def resolve_paths(targets: list[str]) -> tuple[list[Path], list[str]]:
    resolved: list[Path] = []
    missing: list[str] = []

    for target in targets:
        matches = _expand_target(target)
        if matches:
            resolved.extend(matches)
        else:
            missing.append(target)

    return sorted(dict.fromkeys(resolved)), missing


def filter_rules(rules: list[Rule], selected_ids: set[str], ignored_ids: set[str]) -> list[Rule]:
    filtered = rules

    if selected_ids:
        filtered = [rule for rule in filtered if rule.id in selected_ids]

    if ignored_ids:
        filtered = [rule for rule in filtered if rule.id not in ignored_ids]

    return filtered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="suslint",
        description="Lint GitHub Actions workflows for sustainability issues.",
        epilog="Example: suslint .github/workflows/*.yml",
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="Workflow files, directories, or glob patterns to lint",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print errors, not informational output",
    )

    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )

    parser.add_argument(
        "--select",
        action="append",
        default=[],
        help="Only run the specified rule IDs, comma-separated or repeated",
    )

    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Skip the specified rule IDs, comma-separated or repeated",
    )

    return parser


def _validate_rule_selection(selected_ids: set[str], ignored_ids: set[str], rules: list[Rule]) -> None:
    known_rule_ids = {rule.id for rule in rules}
    unknown_rule_ids = sorted((selected_ids | ignored_ids) - known_rule_ids)

    if unknown_rule_ids:
        print(f"error: unknown rule ID(s): {', '.join(unknown_rule_ids)}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    selected_ids = _split_rule_ids(args.select)
    ignored_ids = _split_rule_ids(args.ignore)

    rules = load_rules()
    _validate_rule_selection(selected_ids, ignored_ids, rules)
    active_rules = filter_rules(rules, selected_ids, ignored_ids)
    rule_map = {rule.id: rule for rule in rules}

    paths, missing_targets = resolve_paths(args.files)
    if missing_targets:
        for target in missing_targets:
            print(f"error: target did not match any files: {target}", file=sys.stderr)
        sys.exit(1)

    if not paths:
        print("error: no workflow files found", file=sys.stderr)
        sys.exit(1)

    results: list[FileResult] = [lint_path(path, active_rules) for path in paths]

    if args.format == "json":
        print(render_json(results, rule_map))
    else:
        output = render_text(results, rule_map, quiet=args.quiet)
        if output:
            print(output)

    exit_code = 1 if any(result.error or result.issues for result in results) else 0
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
