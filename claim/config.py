import json
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from claim.workdays import STATES

CONFIG = Path(__file__).resolve().parent.parent / "config.toml"

TEMPLATE = """\
# Your details for fill_claim.py. Change them with `fill_claim.py setup`, or edit here.

name = {name}
file_prefix = {file_prefix}   # output: <MONTH>_<YEAR>_<file_prefix>_YTM_BTEPV4.pdf

# Training period: only days between these dates are filled in.
start_date = {start_date}
end_date = {end_date}

# Your own stamped BTEPV4 form, with page 2 still blank. It is never copied.
form = {form}

# Written on every working day.
time_in = {time_in}
time_out = {time_out}
hours = {hours}

# State whose public holidays are skipped, e.g. SGR (Selangor), KUL (Kuala Lumpur).
state = {state}
"""


class ConfigError(ValueError):
    pass


@dataclass
class Config:
    name: str
    file_prefix: str
    start_date: date
    end_date: date
    form: str
    time_in: str = "8.30"
    time_out: str = "5.30"
    hours: str = "9"
    state: str = "SGR"

    @property
    def form_path(self):
        return Path(self.form).expanduser()


def quoted(text):
    return json.dumps(text, ensure_ascii=False)


def save_config(config, path=CONFIG):
    text = TEMPLATE.format(
        name=quoted(config.name),
        file_prefix=quoted(config.file_prefix),
        start_date=config.start_date.isoformat(),
        end_date=config.end_date.isoformat(),
        form=quoted(config.form),
        time_in=quoted(config.time_in),
        time_out=quoted(config.time_out),
        hours=quoted(config.hours),
        state=quoted(config.state),
    )
    path.write_text(text, encoding="utf-8")


def load_config(path=CONFIG):
    try:
        with path.open("rb") as file:
            config = Config(**tomllib.load(file))
    except (tomllib.TOMLDecodeError, TypeError) as error:
        raise ConfigError(f"{path.name} can't be read ({error}); fix it or run `fill_claim.py setup`") from None
    for field in ("name", "file_prefix", "form", "time_in", "time_out", "hours", "state"):
        value = getattr(config, field)
        if not isinstance(value, str):
            raise ConfigError(f'{field} in {path.name} must be in quotes, like {field} = "{value}"')
    for field in ("start_date", "end_date"):
        if type(getattr(config, field)) is not date:
            raise ConfigError(f"{field} in {path.name} must be a date like 2026-08-10, without quotes or a time")
    if "/" in config.file_prefix:
        raise ConfigError(f"file_prefix in {path.name} can't contain '/', because it becomes part of a file name")
    config.state = config.state.upper()
    if config.state not in STATES:
        raise ConfigError(f"state in {path.name} must be one of: {', '.join(STATES)}")
    return config
