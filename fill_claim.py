import argparse
import calendar
import sys
from datetime import date
from pathlib import Path

from claim.config import CONFIG, ConfigError, load_config
from claim.fill import fill_month
from claim.form import FormLayoutError, check_form
from claim.questions import setup
from claim.workdays import in_training, long_date, malay_day_name, parse_days, public_holidays, working_days


def main(argv=None, config_path=CONFIG, ask=input):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["setup"]:
        setup(config_path, ask)
        return

    parser = argparse.ArgumentParser(
        description="Fill the Yayasan TM practical claim form for one month. "
        "Run 'fill_claim.py setup' to enter or change your details.",
    )
    parser.add_argument("month", type=year_and_month, help="YYYY-MM, e.g. 2026-11")
    parser.add_argument("--skip", type=day_list, default=set(), help="days you did not work, e.g. 7-11,15")
    parser.add_argument("--work", type=day_list, default=set(), help="public holidays (or other days) you did work, e.g. 16")
    parser.add_argument("--date", type=date.fromisoformat, help="signing date, YYYY-MM-DD (default: last working day)")
    parser.add_argument("--out", type=Path, help="output file (default: ~/Downloads/<MONTH>_<YEAR>_<PREFIX>_YTM_BTEPV4.pdf)")
    args = parser.parse_args(argv)
    year, month = args.month

    if not config_path.exists():
        print("No details saved yet, so let's set them up first.")
        setup(config_path, ask)
    try:
        config = load_config(config_path)
        check_form(config.form_path)
    except ConfigError as error:
        parser.error(str(error))
    except ValueError as error:
        parser.error(f"{error}. Run 'fill_claim.py setup' to point to your stamped form.")

    days = working_days(year, month, config, args.skip, args.work)
    if not days:
        parser.error(f"no working days in {year}-{month:02} (training runs {config.start_date} to {config.end_date})")
    month_name = calendar.month_name[month]
    out = args.out or Path.home() / "Downloads" / f"{month_name.upper()}_{year}_{config.file_prefix}_YTM_BTEPV4.pdf"
    if out.exists():
        parser.error(f"{out} already exists; delete it first or pass --out")
    sign_date = args.date or days[-1]

    print_summary(config, year, month, days, sign_date)
    try:
        fill_month(config, out, year, month, days, sign_date)
    except FormLayoutError as error:
        parser.error(str(error))
    print(f"Saved {out}")


def year_and_month(text):
    try:
        year, month = map(int, text.split("-"))
        date(year, month, 1)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' isn't a month like 2026-11") from None
    return year, month


def day_list(text):
    try:
        return parse_days(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def print_summary(config, year, month, days, sign_date):
    print(f"{calendar.month_name[month]} {year}: {len(days)} working days")
    print("  " + ", ".join(f"{d.day} {malay_day_name(d)}" for d in days))
    for d, name in sorted(public_holidays(config, year).items()):
        if d.month == month and d.weekday() < 5 and d not in days and in_training(config, d):
            print(f"  skipped public holiday: {long_date(d)} ({name})")
    print(f"  signing date: {long_date(sign_date)}")


if __name__ == "__main__":
    main()
