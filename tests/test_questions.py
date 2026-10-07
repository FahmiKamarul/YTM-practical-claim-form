import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pymupdf
import pytest

from claim.config import ConfigError, load_config, save_config
from claim.questions import setup, suggested_prefix_for, unquote_dragged_path
from helpers import AHMAD, SITI, answers, make_pdf

TOOL_FOLDER = Path(__file__).resolve().parent.parent


def test_config_round_trips_awkward_text(tmp_path):
    config = replace(AHMAD, name='Zoë "Z" O\\Neil', form="/Users/z/Downloads/(Stamped) YTM_BTEPV4.pdf")
    path = tmp_path / "config.toml"
    save_config(config, path)
    assert load_config(path) == config


def test_config_file_explains_each_setting(tmp_path):
    path = tmp_path / "config.toml"
    save_config(AHMAD, path)
    text = path.read_text()
    assert "# Training period: only days between these dates are filled in." in text
    assert "# State whose public holidays are skipped" in text
    assert "start_date = 2026-08-10\n" in text


def test_config_with_a_missing_field_gives_a_clear_error(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('name = "A"\n')
    with pytest.raises(ConfigError, match="config.toml"):
        load_config(path)


def test_config_with_a_quoted_date_gives_a_clear_error(tmp_path):
    path = tmp_path / "config.toml"
    save_config(AHMAD, path)
    path.write_text(path.read_text().replace("start_date = 2026-08-10", 'start_date = "2026-08-10"'))
    with pytest.raises(ConfigError, match="start_date"):
        load_config(path)


def test_config_with_broken_toml_gives_a_clear_error(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("name = \n")
    with pytest.raises(ConfigError, match="config.toml"):
        load_config(path)


def edited(path, new_line):
    key = new_line.split(" = ")[0]
    lines = [new_line if line.startswith(key + " =") else line for line in path.read_text().splitlines()]
    path.write_text("\n".join(lines) + "\n")


@pytest.mark.parametrize("new_line, field", [
    ("hours = 9", "hours"),
    ("time_in = 8.30", "time_in"),
    ('state = "XYZ"', "state"),
    ("start_date = 2026-08-10T00:00:00", "start_date"),
    ('file_prefix = "RAVI_A/L"', "file_prefix"),
])
def test_config_with_a_wrong_value_names_the_field(tmp_path, new_line, field):
    path = tmp_path / "config.toml"
    save_config(AHMAD, path)
    edited(path, new_line)
    with pytest.raises(ConfigError, match=field):
        load_config(path)


def test_config_accepts_a_lower_case_state(tmp_path):
    path = tmp_path / "config.toml"
    save_config(AHMAD, path)
    edited(path, 'state = "kul"')
    assert load_config(path).state == "KUL"


def test_config_is_saved_as_utf8_on_any_computer(tmp_path):
    path = tmp_path / "config.toml"
    script = (
        "import sys; from dataclasses import replace; from pathlib import Path\n"
        "from claim.config import save_config\n"
        "from helpers import AHMAD\n"
        "save_config(replace(AHMAD, name='Chen \\u9648'), Path(sys.argv[1]))\n"
    )
    env = os.environ | {
        "LC_ALL": "en_US.ISO8859-1",
        "PYTHONUTF8": "0",
        "PYTHONPATH": os.pathsep.join([str(TOOL_FOLDER), str(TOOL_FOLDER / "tests")]),
    }
    subprocess.run([sys.executable, "-c", script, str(path)], env=env, check=True)
    assert load_config(path).name == "Chen \u9648"


def test_setup_saves_answers_and_defaults(tmp_path, stand_in_form):
    path = tmp_path / "config.toml"
    ask = answers(
        "Ahmad Faiz bin Ismail", "", "2026-08-10", "2027-02-09",
        str(stand_in_form), "", "", "", "",
    )
    setup(path, ask)
    assert load_config(path) == replace(AHMAD, form=str(stand_in_form))
    assert "[AHMAD_FAIZ]" in ask.prompts[1]


def test_setup_has_no_default_form(tmp_path, stand_in_form, capsys):
    path = tmp_path / "config.toml"
    ask = answers("A", "", "2026-08-10", "2027-02-09", "", str(stand_in_form), "", "", "", "")
    setup(path, ask)
    assert "[" not in ask.prompts[4]
    assert "Please enter a value." in capsys.readouterr().out


def test_setup_asks_again_after_invalid_answers(tmp_path, stand_in_form, capsys):
    path = tmp_path / "config.toml"
    not_a_pdf = tmp_path / "notes.pdf"
    not_a_pdf.write_text("hello")
    other_pdf = make_pdf(tmp_path / "other.pdf", "Some other form")
    ask = answers(
        "", "Siti Aminah binti Ali",
        "",
        "1/9/2026", "2026-09-01",
        "2026-08-01", "2026-12-31",
        "nope.pdf", str(not_a_pdf), str(other_pdf), str(stand_in_form),
        "9.00", "6.00", "8",
        "XYZ", "kul",
    )
    setup(path, ask)
    assert load_config(path) == replace(SITI, form=str(stand_in_form))
    output = capsys.readouterr().out
    assert "YYYY-MM-DD" in output
    assert "after the start date" in output
    assert "No file at nope.pdf" in output
    assert "notes.pdf is not a PDF" in output
    assert "BEP/02" in output
    assert "KUL" in output


def test_setup_stores_full_path_of_dragged_in_form(tmp_path, monkeypatch):
    form = make_pdf(tmp_path / "(Stamped) YTM_BTEPV4.pdf", "No. Borang : BEP/02", "Versi : 2-01-2025")
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config.toml"
    setup(path, answers("A", "", "2026-08-10", "2027-02-09", r"\(Stamped\)\ YTM_BTEPV4.pdf ", "", "", "", ""))
    assert load_config(path).form == str(form)


def test_setup_rerun_offers_current_answers(tmp_path, stand_in_form):
    path = tmp_path / "config.toml"
    save_config(replace(AHMAD, form=str(stand_in_form)), path)
    setup(path, answers(*[""] * 9))
    assert load_config(path) == replace(AHMAD, form=str(stand_in_form))


def test_setup_rejects_a_month_that_was_already_filled(tmp_path, stand_in_form, capsys):
    doc = pymupdf.open(stand_in_form)
    doc[1].add_freetext_annot(pymupdf.Rect(150, 200, 270, 215), "Selasa")
    filled = tmp_path / "SEPTEMBER_2026_YTM_BTEPV4.pdf"
    doc.save(filled)
    path = tmp_path / "config.toml"
    setup(path, answers("A", "", "2026-08-10", "2027-02-09", str(filled), str(stand_in_form), "", "", "", ""))
    assert "already filled" in capsys.readouterr().out
    assert load_config(path).form == str(stand_in_form)


def test_setup_starts_fresh_when_config_is_broken(tmp_path, stand_in_form, capsys):
    path = tmp_path / "config.toml"
    path.write_text("name = \n")
    setup(path, answers("A", "", "2026-08-10", "2027-02-09", str(stand_in_form), "", "", "", ""))
    assert "couldn't be read" in capsys.readouterr().out
    assert load_config(path).name == "A"


def test_setup_suggests_a_prefix_that_can_be_a_file_name(tmp_path, stand_in_form):
    path = tmp_path / "config.toml"
    ask = answers("Ravi a/l Muthu", "", "2026-08-10", "2027-02-09", str(stand_in_form), "", "", "", "")
    setup(path, ask)
    assert "/" not in load_config(path).file_prefix


def test_dragged_windows_path_keeps_its_backslashes():
    dragged = '"C:\\Users\\siti\\Downloads\\(Stamped) YTM_BTEPV4.pdf"'
    assert unquote_dragged_path(dragged, windows=True) == "C:\\Users\\siti\\Downloads\\(Stamped) YTM_BTEPV4.pdf"


def test_dragged_mac_path_loses_its_escapes():
    dragged = "/Users/siti/Downloads/\\(Stamped\\)\\ YTM_BTEPV4.pdf"
    assert unquote_dragged_path(dragged, windows=False) == "/Users/siti/Downloads/(Stamped) YTM_BTEPV4.pdf"


@pytest.mark.parametrize("name, prefix", [
    ("Farah binti Osman", "FARAH"),
    ("Ravi a/l Kumar", "RAVI"),
    ("Ahmad Faiz bin Ismail", "AHMAD_FAIZ"),
    ("Lim Mei Ling", "LIM_MEI"),
])
def test_suggested_prefix_stops_before_bin_binti_al_ap(name, prefix):
    assert suggested_prefix_for(name) == prefix
