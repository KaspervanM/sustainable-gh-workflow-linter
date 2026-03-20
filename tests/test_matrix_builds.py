from pathlib import Path

from suslint.core import lint
from suslint.rules.matrix_builds import RULE


def test_reports_large_cross_product_matrix(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Matrix Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ${{ matrix.os }}\n"
        "    timeout-minutes: 10\n"
        "    strategy:\n"
        "      matrix:\n"
        "        os: [ubuntu-latest, windows-latest, macos-latest]\n"
        "        node: [18, 20, 22]\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS009"
    assert issues[0].message == (
        "job 'test' defines a matrix with 9 combinations, which may create excessive runner usage"
    )
    assert issues[0].location is not None
    assert issues[0].location.trail == "jobs.test.strategy.matrix"
    assert issues[0].location.line == 8
    assert issues[0].location.col == 5


def test_does_not_report_small_matrix(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Matrix Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ${{ matrix.os }}\n"
        "    timeout-minutes: 10\n"
        "    strategy:\n"
        "      matrix:\n"
        "        os: [ubuntu-latest, windows-latest]\n"
        "        node: [18, 20]\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []


def test_reports_large_single_axis_matrix(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Matrix Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    strategy:\n"
        "      matrix:\n"
        "        python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS009"


def test_reports_large_include_only_matrix(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Matrix Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    strategy:\n"
        "      matrix:\n"
        "        include:\n"
        "          - os: ubuntu-latest\n"
        "            node: 18\n"
        "          - os: ubuntu-latest\n"
        "            node: 20\n"
        "          - os: windows-latest\n"
        "            node: 18\n"
        "          - os: windows-latest\n"
        "            node: 20\n"
        "          - os: macos-latest\n"
        "            node: 20\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert len(issues) == 1
    assert issues[0].rule_id == "SUS009"


def test_ignores_unrecognized_dynamic_matrix_shape(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "name: Matrix Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    strategy:\n"
        "      matrix:\n"
        "        version: ${{ fromJson(needs.prepare.outputs.versions) }}\n"
        "    steps:\n"
        "      - run: echo test\n",
        encoding="utf-8",
    )

    issues = lint(workflow, [RULE])

    assert issues == []