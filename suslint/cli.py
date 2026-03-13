from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from suslint.rule import Rule
from suslint.core import lint, load_rules


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="suslint",
        description="Lint GitHub Actions workflows for sustainability issues.",
        epilog="Example: suslint .github/workflows/*.yml",
    )

    parser.add_argument(
        "files",
        type=Path,
        nargs="+",
        help="Workflow YAML files to lint",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print errors, not informational output",
    )

    return parser


def lint_file(path: Path, rules: Iterable[Rule], quiet: bool) -> int:
    if not path.exists():
        print(f"error: file does not exist: {path}", file=sys.stderr)
        return 1

    issues = lint(path, rules)

    if not issues:
        if not quiet:
            print(f"Success: no issues found in {path}")
        return 0

    print(f"{path}:")

    for issue in issues:
        if issue.location:
            print(f"  {issue.rule_id} {issue.location}: {issue.message}")
        else:
            print(f"  {issue.rule_id}: {issue.message}")

    return 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    exit_code = 0
    rules = load_rules()

    for path in args.files:
        result = lint_file(path, rules, args.quiet)
        exit_code = max(exit_code, result)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()