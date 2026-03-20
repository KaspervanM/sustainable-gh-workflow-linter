from pathlib import Path

import pytest

from suslint.core import LintError, count_affected_files, count_issues, lint
from suslint.rules.dependency_caching import RULE as dc_RULE
from suslint.rules.job_timeout import RULE as jt_RULE


def test_ignore_comment(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "concurrency:\n"
        "  group: ci-${{ github.workflow }}-${{ github.ref }}\n"
        "  cancel-in-progress: true\n"     
        "jobs:\n"
        "  build: # suslint ignore: SUS002\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [jt_RULE])

    assert issues == []


def test_wrong_ignore_comment(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "concurrency:\n"
        "  group: ci-${{ github.workflow }}-${{ github.ref }}\n"
        "  cancel-in-progress: true\n"     
        "jobs:\n"
        "  build: # suslint ignore: SUS001\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [jt_RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS002"
    assert issues[0].message == "job 'build' has no timeout-minutes"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build"
    assert issues[0].location.line == 8
    assert issues[0].location.col == 3


def test_multiple_errors_no_ignore_comments(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "      - uses: actions/setup-node@v6\n"
        "        with:\n"
        "          node-version: '20'\n"
        "      - run: npm ci\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [dc_RULE, jt_RULE])

    assert len(issues) == 2
    assert issues[0].rule_id == "SUS001"
    assert issues[0].message == "job 'build' installs dependencies without using dependency caching"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build"
    assert issues[0].location.line == 5
    assert issues[0].location.col == 3
    assert issues[1].rule_id == "SUS002"
    assert issues[1].message == "job 'build' has no timeout-minutes"
    assert issues[1].location is not None
    assert issues[1].location.trail == "jobs.build"
    assert issues[1].location.line == 5
    assert issues[1].location.col == 3


def test_multiple_errors_one_ignore_comment_1(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build: # suslint ignore: SUS001\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "      - uses: actions/setup-node@v6\n"
        "        with:\n"
        "          node-version: '20'\n"
        "      - run: npm ci\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [dc_RULE, jt_RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS002"
    assert issues[0].message == "job 'build' has no timeout-minutes"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build"
    assert issues[0].location.line == 5
    assert issues[0].location.col == 3


def test_multiple_errors_one_ignore_comment_2(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build: # suslint ignore: SUS002\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "      - uses: actions/setup-node@v6\n"
        "        with:\n"
        "          node-version: '20'\n"
        "      - run: npm ci\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [dc_RULE, jt_RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS001"
    assert issues[0].message == "job 'build' installs dependencies without using dependency caching"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.build"
    assert issues[0].location.line == 5
    assert issues[0].location.col == 3


def test_multiple_errors_two_ignore_comments(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build: # suslint ignore: SUS001, SUS002\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "      - uses: actions/setup-node@v6\n"
        "        with:\n"
        "          node-version: '20'\n"
        "      - run: npm ci\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [dc_RULE, jt_RULE])

    assert issues == []
