from datetime import date
from pathlib import Path

import pymupdf
import pytest

from claim.fill import fill_month
from claim.form import ClaimForm, FormLayoutError, check_form
from claim.workdays import parse_days, working_days
from helpers import FORM, AHMAD, SITI, flattened, needs_form, spans, texts

TOOL_FOLDER = Path(__file__).resolve().parent.parent


@needs_form
def test_the_blank_stamped_form_passes_the_check():
    check_form(FORM)


@needs_form
def test_labels_are_found_where_expected():
    form = ClaimForm(FORM)
    claim, timesheet = form.page(1), form.page(2)
    assert round(claim.find("Tarikh / Date", below="Pengakuan Pelajar").y0) == 576
    assert round(claim.find("Tarikh / Date", below="Pengesahan Penyelia").y0) == 711
    assert round(timesheet.find("Month").y0) == 100
    assert round(timesheet.find("HARI / DAY").y0) == 158


def test_missing_label_is_named_in_the_error(stand_in_form):
    page = ClaimForm(stand_in_form).page(2)
    with pytest.raises(FormLayoutError, match="Couldn't find 'Month' on page 2"):
        page.write_after("Month", "11")


@needs_form
def test_value_starts_just_after_the_colon(tmp_path):
    form = ClaimForm(FORM)
    timesheet = form.page(2)
    timesheet.write_after("Month", "11")
    out = tmp_path / "out.pdf"
    form.save(out)
    page = pymupdf.open(out)[1]
    month = page.search_for("Month")[0]
    colon = min((c for c in page.search_for(":") if c.x0 > month.x0 and abs(c.y0 - month.y0) < 2), key=lambda c: c.x0)
    header_line = spans(flattened(pymupdf.open(out))[1])
    (written,) = [x0 for text, x0, baseline in header_line if text == "11" and baseline < month.y1]
    assert colon.x1 < written < colon.x1 + 7


@needs_form
def test_long_name_stays_on_one_line(tmp_path):
    name = "Muhammad Aiman Hakimi bin Mohd Zulkifli Al-Hafiz Abdullah"
    form = ClaimForm(FORM)
    form.page(2).write_after("Name", name)
    out = tmp_path / "out.pdf"
    form.save(out)
    assert name in [text for text, _, _ in spans(flattened(pymupdf.open(out))[1])]


def test_no_form_is_kept_in_the_tool_folder():
    pdfs = [p for p in TOOL_FOLDER.rglob("*.pdf") if ".venv" not in p.parts]
    assert pdfs == []


@pytest.fixture
def september(tmp_path):
    out = tmp_path / "sep.pdf"
    days = working_days(2026, 9, AHMAD, skip=parse_days("7-11"), work={16})
    fill_month(AHMAD, out, 2026, 9, days, sign_date=date(2026, 9, 30))
    return pymupdf.open(out)


@needs_form
def test_page2_header(september):
    assert texts(september[1])[:3] == ["Ahmad Faiz bin Ismail", "2026", "9"]


@needs_form
def test_page2_rows_only_for_working_days(september):
    assert len(texts(september[1])) == 3 + 17 * 4


@needs_form
def test_page2_text_sits_on_the_row_of_its_date(september):
    printed = {
        int(text): baseline
        for text, x0, baseline in spans(pymupdf.open(FORM)[1])
        if x0 < 142 and text.isdigit() and baseline > 190
    }
    filled = {}
    for text, x0, baseline in spans(flattened(september)[1]):
        if x0 < 142 or baseline < 190 or baseline > 640:
            continue
        day = min(printed, key=lambda d: abs(printed[d] - baseline))
        assert abs(printed[day] - baseline) < 1, (text, day, baseline)
        filled.setdefault(day, []).append((x0, text))
    filled = {day: [text for _, text in sorted(cells)] for day, cells in filled.items()}
    assert filled[1] == ["Selasa", "8.30", "5.30", "9"]
    assert filled[16] == ["Rabu", "8.30", "5.30", "9"]
    assert filled[28] == ["Isnin", "8.30", "5.30", "9"]
    assert sorted(filled) == [d.day for d in working_days(2026, 9, AHMAD, skip=parse_days("7-11"), work={16})]


@needs_form
def test_page1_working_days_sits_between_its_label_and_dotted_line(september):
    printed = spans(pymupdf.open(FORM)[0])
    (dots,) = [b for t, x0, b in printed if t.startswith("....") and 470 < b < 490]
    (label,) = [b for t, x0, b in printed if t.startswith("Jumlah hari bekerja")]
    (count,) = [b for t, x0, b in spans(flattened(september)[0]) if t == "17"]
    digit_height = 0.72 * 11
    assert count < dots - 2
    assert count - digit_height > label + 1


@needs_form
def test_page1_count_and_dates(september):
    form_texts = texts(pymupdf.open(FORM)[0])
    assert texts(september[0]) == form_texts + ["17", "30 September 2026", "30 September 2026"]


@needs_form
def test_form_uses_name_and_hours_from_config(tmp_path):
    out = tmp_path / "siti.pdf"
    fill_month(SITI, out, 2026, 9, working_days(2026, 9, SITI), sign_date=date(2026, 9, 30))
    page2 = texts(pymupdf.open(out)[1])
    assert page2[:3] == ["Siti Aminah binti Ali", "2026", "9"]
    assert page2[3:7] == ["Selasa", "9.00", "6.00", "8"]
