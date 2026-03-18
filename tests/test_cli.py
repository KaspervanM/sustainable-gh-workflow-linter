import json
from pathlib import Path

import pytest

from suslint import cli


def test_main_exits_zero_and_prints_success_for_clean_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "clean.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "    branches:\n"
        "      - main\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert f"Success: no issues found in {workflow.resolve()}" in captured.out
    assert captured.err == ""


def test_main_exits_one_and_prints_issues_and_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert f"{workflow.resolve()}:" in captured.out
    assert "SUS002 [warning/runner-efficiency] jobs.build" in captured.out
    assert "SUS003 [warning/trigger-scope] on.push" in captured.out
    assert "Summary: 2 issues across 1 file." in captured.out
    assert captured.err == ""


def test_main_supports_directory_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "clean.yml").write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n",
        encoding="utf-8",
    )
    (workflows_dir / "bad.yaml").write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", str(tmp_path)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "clean.yml" in captured.out
    assert "bad.yaml" in captured.out
    assert "Summary: 2 issues across 1 file." in captured.out


def test_main_supports_glob_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    first = tmp_path / "a.yml"
    second = tmp_path / "b.yml"
    first.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n",
        encoding="utf-8",
    )
    second.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", str(tmp_path / "*.yml")])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert f"{first.resolve()}:" not in captured.out
    assert f"{second.resolve()}:" in captured.out


def test_main_supports_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", "--format", "json", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exc_info.value.code == 1
    assert payload["summary"] == {"issues": 2, "files_with_issues": 1}
    assert payload["files"][0]["path"] == str(workflow.resolve())
    assert payload["files"][0]["issues"][0]["severity"] == "warning"
    assert payload["files"][0]["issues"][0]["category"]
    assert payload["files"][0]["issues"][0]["remediation"]
    assert captured.err == ""


def test_main_supports_rule_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", "--select", "SUS002", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "SUS002" in captured.out
    assert "SUS003" not in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out


def test_main_supports_rule_ignoring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  push:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", "--ignore", "SUS002", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "SUS002" not in captured.out
    assert "SUS003" in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out


def test_main_exits_one_for_unknown_rule_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "clean.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", "--select", "SUS999", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "error: unknown rule ID(s): SUS999" in captured.err


def test_main_exits_one_for_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    missing_file = tmp_path / "missing.yml"

    monkeypatch.setattr("sys.argv", ["suslint", str(missing_file)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert captured.out == ""
    assert f"error: target did not match any files: {missing_file}" in captured.err


def test_main_prints_clean_error_for_invalid_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "invalid.yml"
    workflow.write_text("on:\n  push: [\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["suslint", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert f"{workflow.resolve()}:" in captured.out
    assert "error: failed to parse YAML:" in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out
    assert captured.err == ""


def test_main_prints_clean_error_for_non_mapping_top_level_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "invalid-shape.yml"
    workflow.write_text("- just\n- a\n- list\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["suslint", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert f"{workflow.resolve()}:" in captured.out
    assert "error: workflow file must contain a mapping at the top level" in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out
    assert captured.err == ""


def test_main_reports_dependency_caching_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "cache-miss.yml"
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
        "      - uses: actions/setup-node@v6\n"
        "        with:\n"
        "          node-version: '20'\n"
        "      - run: npm ci\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", "--select", "SUS001", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "SUS001 [warning/runner-efficiency] jobs.build" in captured.out
    assert "installs dependencies without using dependency caching" in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out
    assert captured.err == ""


def test_main_reports_artifact_reuse_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "artifact-reuse.yml"
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

    monkeypatch.setattr("sys.argv", ["suslint", "--select", "SUS005", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "SUS005 [warning/runner-efficiency] jobs.package" in captured.out
    assert "appears to rebuild 'npm-build' outputs already built in job 'build'" in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out
    assert captured.err == ""


def test_main_reports_parallelization_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "parallelization.yml"
    workflow.write_text(
        "name: Example\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo build\n"
        "  package:\n"
        "    runs-on: ubuntu-latest\n"
        "    needs: build\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo package\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", "--select", "SUS006", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "SUS006 [warning/runner-efficiency] jobs.package" in captured.out
    assert "may be unnecessarily serialized" in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out
    assert captured.err == ""
    

def test_main_reports_shallow_clone_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = tmp_path / "shallow-clone.yml"
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
        "      - run: echo hello\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["suslint", "--select", "SUS007", str(workflow)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "SUS007 [warning/runner-efficiency] jobs.build.steps[0]" in captured.out
    assert "does not use fetch-depth: 1" in captured.out
    assert "Summary: 1 issue across 1 file." in captured.out
    assert captured.err == ""