from pathlib import Path

from suslint.core import lint
from suslint.rules.artifact_reuse import RULE


def test_reports_repeated_builds_without_artifact_reuse(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          fetch-depth: 1\n"
        "      - run: npm run build\n"
        "  package:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          fetch-depth: 1\n"
        "      - run: npm run build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS005"
    assert issues[0].message == (
        "job 'package' appears to rebuild 'npm-build' outputs already built in job 'build' "
        "without artifact reuse"
    )
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.package"
    assert issues[0].location.line == 13
    assert issues[0].location.col == 3


def test_does_not_report_single_build_job(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: npm run build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_different_build_types(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  web:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: npm run build\n"
        "  backend:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: mvn package\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_artifact_upload_and_download_are_used(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: npm run build\n"
        "      - uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: web-dist\n"
        "          path: dist/\n"
        "  package:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/download-artifact@v4\n"
        "        with:\n"
        "          name: web-dist\n"
        "      - run: npm run build\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_reports_only_duplicate_jobs_after_first_match(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build1:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: pyinstaller suslint/cli.py\n"
        "  build2:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: pyinstaller suslint/cli.py\n"
        "  build3:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: pyinstaller suslint/cli.py\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 2
    assert [issue.location.trail for issue in issues if issue.location is not None] == [
        "jobs.build2",
        "jobs.build3",
    ]