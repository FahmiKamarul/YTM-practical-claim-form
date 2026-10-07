from dataclasses import replace

import pymupdf
import pytest

from claim.config import load_config, save_config
from fill_claim import main
from helpers import FORM, AHMAD, SITI, answers, make_pdf, needs_form, texts


def config_with_form(tmp_path, form, base=AHMAD):
    path = tmp_path / "config.toml"
    save_config(replace(base, form=str(form)), path)
    return path


@needs_form
def test_cli_defaults_sign_date_to_last_working_day(tmp_path, ahmad_config):
    out = tmp_path / "oct.pdf"
    main(["2026-10", "--out", str(out)], config_path=ahmad_config)
    assert texts(pymupdf.open(out)[0])[-2:] == ["30 October 2026", "30 October 2026"]


@needs_form
def test_cli_names_file_with_prefix_in_downloads(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "Downloads").mkdir()
    path = tmp_path / "config.toml"
    save_config(SITI, path)
    main(["2026-10"], config_path=path)
    assert (tmp_path / "Downloads" / "OCTOBER_2026_SITI_AMINAH_YTM_BTEPV4.pdf").exists()


def test_cli_refuses_to_overwrite(tmp_path, stand_in_form):
    path = config_with_form(tmp_path, stand_in_form)
    out = tmp_path / "oct.pdf"
    out.write_bytes(b"submitted")
    with pytest.raises(SystemExit):
        main(["2026-10", "--out", str(out)], config_path=path)
    assert out.read_bytes() == b"submitted"


def test_cli_rejects_month_outside_training(tmp_path, stand_in_form):
    path = config_with_form(tmp_path, stand_in_form)
    with pytest.raises(SystemExit):
        main(["2026-07", "--out", str(tmp_path / "jul.pdf")], config_path=path)


@needs_form
def test_cli_summary_only_lists_holidays_inside_training(tmp_path, ahmad_config, capsys):
    main(["2027-02", "--out", str(tmp_path / "feb.pdf")], config_path=ahmad_config)
    output = capsys.readouterr().out
    assert "8 February 2027" in output
    assert "24 February 2027" not in output


def test_cli_setup_command_saves_config(tmp_path, stand_in_form):
    path = tmp_path / "config.toml"
    main(["setup"], config_path=path, ask=answers("Siti Aminah binti Ali", "", "2026-09-01", "2026-12-31",
                                                  str(stand_in_form), "9.00", "6.00", "8", "KUL"))
    assert load_config(path) == replace(SITI, form=str(stand_in_form))


@needs_form
def test_cli_runs_setup_first_when_there_is_no_config(tmp_path):
    path = tmp_path / "config.toml"
    out = tmp_path / "oct.pdf"
    ask = answers("Ahmad Faiz bin Ismail", "", "2026-08-10", "2027-02-09", str(FORM), "", "", "", "")
    main(["2026-10", "--out", str(out)], config_path=path, ask=ask)
    assert load_config(path) == AHMAD
    assert out.exists()


def test_cli_explains_a_moved_form(tmp_path, capsys):
    path = config_with_form(tmp_path, tmp_path / "moved.pdf")
    with pytest.raises(SystemExit):
        main(["2026-10", "--out", str(tmp_path / "oct.pdf")], config_path=path)
    assert "fill_claim.py setup" in capsys.readouterr().err


def test_cli_rejects_a_form_that_is_not_btepv4(tmp_path, capsys):
    path = config_with_form(tmp_path, make_pdf(tmp_path / "other.pdf", "Some other form"))
    with pytest.raises(SystemExit):
        main(["2026-10", "--out", str(tmp_path / "oct.pdf")], config_path=path)
    assert "BEP/02" in capsys.readouterr().err


def test_cli_reports_a_missing_label(tmp_path, stand_in_form, capsys):
    path = config_with_form(tmp_path, stand_in_form)
    out = tmp_path / "oct.pdf"
    with pytest.raises(SystemExit):
        main(["2026-10", "--out", str(out)], config_path=path)
    assert "Couldn't find" in capsys.readouterr().err
    assert not out.exists()


@pytest.mark.parametrize("month", ["2026-13", "Nov", "2026"])
def test_cli_rejects_a_malformed_month(tmp_path, stand_in_form, capsys, month):
    path = config_with_form(tmp_path, stand_in_form)
    with pytest.raises(SystemExit):
        main([month], config_path=path)
    assert "like 2026-11" in capsys.readouterr().err


def test_cli_rejects_malformed_skip(tmp_path, stand_in_form, capsys):
    path = config_with_form(tmp_path, stand_in_form)
    with pytest.raises(SystemExit):
        main(["2026-10", "--skip", "7–11"], config_path=path)
    assert "list of days like 7-11,15" in capsys.readouterr().err


def test_cli_explains_a_broken_config(tmp_path, capsys):
    path = tmp_path / "config.toml"
    path.write_text("name = \n")
    with pytest.raises(SystemExit):
        main(["2026-10"], config_path=path)
    assert "config.toml" in capsys.readouterr().err
