from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from suslint.rule import Rule
from suslint.core import load_rules, lint_file


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


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    exit_code = 0
    rules = load_rules()

    for path in args.files:
        if not path.exists():
            print(f"error: file does not exist: {path}", file=sys.stderr)
            sys.exit(1)
        result = lint_file(path, rules)
        if result == 0 and not args.quiet:
            print(f"Success: no issues found in {path}")
        exit_code = max(exit_code, result)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()