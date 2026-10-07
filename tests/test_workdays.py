from datetime import date

import pytest

from claim.workdays import long_date, malay_day_name, parse_days, working_days
from helpers import AHMAD, SITI, days


def test_august_starts_at_training_start_and_skips_holidays():
    assert days(working_days(2026, 8, AHMAD)) == [
        10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 24, 26, 27, 28,
    ]


def test_september_with_leave_and_worked_holiday():
    result = working_days(2026, 9, AHMAD, skip={7, 8, 9, 10, 11}, work={16})
    assert days(result) == [
        1, 2, 3, 4, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 28, 29, 30,
    ]
    assert len(result) == 17


def test_october_is_every_weekday():
    assert days(working_days(2026, 10, AHMAD)) == [
        1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16,
        19, 20, 21, 22, 23, 26, 27, 28, 29, 30,
    ]


def test_february_stops_at_training_end_and_skips_cny_replacement():
    assert days(working_days(2027, 2, AHMAD)) == [1, 2, 3, 4, 5, 9]


def test_work_ignores_days_outside_training():
    assert date(2026, 8, 3) not in working_days(2026, 8, AHMAD, work={3})
    assert date(2027, 2, 10) not in working_days(2027, 2, AHMAD, work={10})


def test_holidays_follow_the_configured_state():
    assert date(2026, 12, 11) not in working_days(2026, 12, AHMAD)
    assert date(2026, 12, 11) in working_days(2026, 12, SITI)


def test_training_period_follows_the_config():
    assert days(working_days(2026, 9, SITI))[:2] == [1, 2]
    assert working_days(2027, 1, SITI) == []


def test_parse_days_accepts_ranges_and_singles():
    assert parse_days("7-11,16") == {7, 8, 9, 10, 11, 16}
    assert parse_days("") == set()


@pytest.mark.parametrize("spec", ["7–11", "a", "7-", "11-7", "45", "0"])
def test_parse_days_explains_bad_input(spec):
    with pytest.raises(ValueError, match="list of days like 7-11,15"):
        parse_days(spec)


def test_day_names_are_malay():
    assert malay_day_name(date(2026, 9, 1)) == "Selasa"
    assert malay_day_name(date(2026, 9, 6)) == "Ahad"


def test_long_date_spells_out_the_month():
    assert long_date(date(2026, 9, 30)) == "30 September 2026"
