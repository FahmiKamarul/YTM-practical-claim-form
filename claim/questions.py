import os
import re
from datetime import date
from pathlib import Path

from claim.config import CONFIG, Config, ConfigError, load_config, save_config
from claim.form import check_form
from claim.workdays import STATES

ON_WINDOWS = os.name == "nt"
NAME_LINKS = {"bin", "binti", "bt", "bte", "a/l", "a/p", "s/o", "d/o"}
BLANK = Config(name="", file_prefix="", start_date=None, end_date=None, form="")


def setup(path=CONFIG, ask=input):
    current = BLANK
    if path.exists():
        try:
            current = load_config(path)
        except ConfigError:
            print(f"Your {path.name} couldn't be read, so starting from scratch.")
    print("Enter your details. Press Enter to keep the value in [brackets].")

    name = ask_until_valid(ask, "Full name", current.name)
    suggested_prefix = current.file_prefix or suggested_prefix_for(name)
    file_prefix = ask_until_valid(ask, "File prefix", suggested_prefix, file_prefix_from)
    start_date = ask_until_valid(ask, "Training start date (YYYY-MM-DD)", current.start_date, parse_iso_date)

    def parse_end_date(text):
        end = parse_iso_date(text)
        if end <= start_date:
            raise ValueError(f"The end date must be after the start date ({start_date}).")
        return end

    end_date = ask_until_valid(ask, "Training end date (YYYY-MM-DD)", current.end_date, parse_end_date)
    form = ask_until_valid(ask, "Path to your stamped BTEPV4 form", current.form, parse_form)
    time_in = ask_until_valid(ask, "Time in", current.time_in)
    time_out = ask_until_valid(ask, "Time out", current.time_out)
    hours = ask_until_valid(ask, "Total hours", current.hours)
    state = ask_until_valid(ask, "State for public holidays, e.g. SGR or KUL", current.state, parse_state)

    config = Config(name, file_prefix, start_date, end_date, form, time_in, time_out, hours, state)
    save_config(config, path)
    print(f"Saved {path}")
    return config


def ask_until_valid(ask, label, default=None, parse=str):
    hint = f" [{default}]" if default else ""
    while True:
        answer = ask(f"{label}{hint}: ").strip() or (str(default) if default else "")
        if not answer:
            print("  Please enter a value.")
            continue
        try:
            return parse(answer)
        except ValueError as error:
            print(f"  {error}")


def suggested_prefix_for(name):
    words = []
    for word in name.split():
        if word.lower().rstrip(".") in NAME_LINKS:
            break
        words.append(word)
    return file_prefix_from(" ".join(words[:2]))


def file_prefix_from(text):
    return "_".join(text.upper().replace("/", "").split())


def parse_iso_date(text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"'{text}' is not a date. Use YYYY-MM-DD, e.g. 2026-08-10.") from None


def parse_form(text):
    path = Path(unquote_dragged_path(text)).expanduser()
    check_form(path)
    return str(path.resolve())


def unquote_dragged_path(text, windows=ON_WINDOWS):
    text = text.strip("'\"")
    if not windows:
        text = re.sub(r"\\(.)", r"\1", text)
    return text


def parse_state(text):
    if text.upper() not in STATES:
        raise ValueError(f"Unknown state code '{text}'. Use one of: {', '.join(STATES)}")
    return text.upper()
