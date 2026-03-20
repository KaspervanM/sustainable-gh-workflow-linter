from pathlib import Path

from suslint.core import lint
from suslint.rules.parallelization import RULE


def test_reports_job_with_needs_but_no_apparent_dependency_use(tmp_path: Path) -> None:
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
        "  package:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: build\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo packaging\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS006"
    assert issues[0].message == (
        "job 'package' uses needs=['build'] but does not appear to consume artifacts or outputs "
        "from upstream jobs and may be unnecessarily serialized"
    )
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.package"
    assert issues[0].location.line == 10
    assert issues[0].location.col == 3


def test_does_not_report_job_without_needs(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  lint:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo linting\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_job_downloads_artifacts(tmp_path: Path) -> None:
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
        "          name: dist\n"
        "          path: dist/\n"
        "  package:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: build\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/download-artifact@v4\n"
        "        with:\n"
        "          name: dist\n"
        "      - run: echo packaging\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_does_not_report_when_job_references_needs_outputs(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  version:\n"
        "    runs-on: ubuntu-latest\n"
        "    outputs:\n"
        "      tag: ${{ steps.meta.outputs.tag }}\n"
        "    steps:\n"
        "      - id: meta\n"
        "        run: echo tag=v1 >> $GITHUB_OUTPUT\n"
        "  publish:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: version\n"
        "    timeout-minutes: 10\n"
        "    env:\n"
        "      TAG: ${{ needs.version.outputs.tag }}\n"
        "    steps:\n"
        "      - run: echo $TAG\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_supports_multiple_needs_values(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  lint:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo lint\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo test\n"
        "  report:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs:\n"
        "      - lint\n"
        "      - test\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo report\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS006"
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.report"