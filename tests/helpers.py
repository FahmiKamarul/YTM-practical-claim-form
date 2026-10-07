from datetime import date

import pymupdf
import pytest

from claim.config import CONFIG, Config, ConfigError, load_config


def _configured_form():
    try:
        return load_config(CONFIG).form_path if CONFIG.exists() else None
    except ConfigError:
        return None


FORM = _configured_form()
needs_form = pytest.mark.skipif(
    FORM is None or not FORM.is_file(),
    reason="no stamped BTEPV4 form set up; run `fill_claim.py setup` to enable this test",
)

AHMAD = Config(
    name="Ahmad Faiz bin Ismail",
    file_prefix="AHMAD_FAIZ",
    start_date=date(2026, 8, 10),
    end_date=date(2027, 2, 9),
    form=str(FORM),
)

SITI = Config(
    name="Siti Aminah binti Ali",
    file_prefix="SITI_AMINAH",
    start_date=date(2026, 9, 1),
    end_date=date(2026, 12, 31),
    form=str(FORM),
    time_in="9.00",
    time_out="6.00",
    hours="8",
    state="KUL",
)


def days(dates):
    return [d.day for d in dates]


def answers(*replies):
    replies = list(replies)

    def ask(prompt):
        ask.prompts.append(prompt)
        return replies.pop(0)

    ask.prompts = []
    return ask


def make_pdf(path, *first_page_lines, pages=2):
    doc = pymupdf.open()
    for _ in range(pages):
        doc.new_page()
    for i, line in enumerate(first_page_lines):
        doc[0].insert_text((72, 72 + 20 * i), line)
    doc.save(path)
    return path


def annots(page):
    return [(a.info["content"], a.rect) for a in page.annots() if a.type[1] == "FreeText"]


def texts(page):
    return [content for content, _ in annots(page)]


def spans(page):
    result = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                if span["text"].strip():
                    result.append((span["text"].strip(), span["bbox"][0], span["origin"][1]))
    return result


def flattened(doc):
    doc.bake()
    return doc
