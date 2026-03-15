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
    assert f"Success: no issues found in {workflow}" in captured.out
    assert captured.err == ""


def test_main_exits_one_and_prints_issues(
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
    assert f"{workflow}:" in captured.out
    assert "SUS001 jobs.build" in captured.out
    assert "SUS002 on.push" in captured.out
    assert captured.err == ""


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
    assert f"error: file does not exist: {missing_file}" in captured.err
