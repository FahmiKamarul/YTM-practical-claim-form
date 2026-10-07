from functools import cached_property

import pymupdf

from claim.workdays import MALAY_DAYS

FORM_MARKERS = ("BEP/02", "2-01-2025")

FONT_SIZE = 11
CAP_HEIGHT = 0.72 * FONT_SIZE
GAP_AFTER_COLON = 4.7
LIFT = 7
ABOVE_DOTS = 3
FIRST_BASELINE = 0.8 * FONT_SIZE


class FormLayoutError(ValueError):
    pass


def check_form(path):
    if not path.is_file():
        raise ValueError(f"No file at {path}")
    try:
        form = ClaimForm(path)
    except pymupdf.FileDataError:
        raise ValueError(f"{path} is not a PDF") from None
    if not form.is_btepv4():
        raise ValueError(
            f"{path.name} doesn't look like the BTEPV4 claim form "
            "(expected 2 pages with 'No. Borang : BEP/02' and 'Versi : 2-01-2025')"
        )
    if form.is_filled():
        raise ValueError(f"{path.name} is a month that was already filled in; use your blank stamped form")


class ClaimForm:
    def __init__(self, path):
        self.doc = pymupdf.open(path, filetype="pdf")

    def page(self, number):
        return FormPage(self.doc[number - 1], number)

    def is_btepv4(self):
        return self.doc.page_count == 2 and all(marker in self.doc[0].get_text() for marker in FORM_MARKERS)

    def is_filled(self):
        timesheet = self.doc[1]
        return bool(timesheet.first_annot) or any(day in timesheet.get_text() for day in MALAY_DAYS)

    def save(self, out):
        self.doc.save(out, garbage=3, deflate=True)


class FormPage:
    def __init__(self, page, number):
        self.page = page
        self.number = number

    def find(self, label, below=None):
        top = self.find(below).y1 if below else 0
        matches = [box for box in self.page.search_for(label) if box.y0 >= top]
        if not matches:
            under = f" under '{below}'" if below else ""
            raise FormLayoutError(f"Couldn't find '{label}'{under} on page {self.number} of the form")
        return min(matches, key=lambda box: (box.y0, box.x0))

    def write_after(self, label, text, below=None):
        box = self.find(label, below)
        colons = [c for c in self.page.search_for(":") if c.x0 >= box.x0 and same_line(c, box)]
        if not colons:
            raise FormLayoutError(f"No colon after '{label}' on page {self.number} of the form")
        colon = min(colons, key=lambda c: c.x0)
        self.write_at(colon.x1 + GAP_AFTER_COLON, box.y1 - LIFT, text)

    def write_on_line_below(self, label, text):
        box = self.find(label)
        strip = pymupdf.Rect(0, box.y1, self.page.rect.width, box.y1 + 2 * box.height)
        dots = self.page.search_for("....", clip=strip)
        if not dots:
            raise FormLayoutError(f"No dotted line below '{label}' on page {self.number} of the form")
        first = min(dots, key=lambda d: d.y0)
        line = pymupdf.Rect(first)
        for d in dots:
            if same_line(d, first):
                line |= d
        self.write_at(line.x0, self.baseline_of(line) - ABOVE_DOTS, text, right=line.x1, align=pymupdf.TEXT_ALIGN_CENTER)

    def baseline_of(self, box):
        for block in self.page.get_text("dict", clip=box)["blocks"]:
            for line in block.get("lines", []):
                return line["spans"][0]["origin"][1]
        raise FormLayoutError(f"No printed text inside {box} on page {self.number} of the form")

    def table_row(self, date_number):
        return TableRow(self, date_number)

    @cached_property
    def ruling_lines(self):
        xs, ys = set(), set()
        for drawing in self.page.get_drawings():
            for kind, *rest in drawing["items"]:
                if kind != "re":
                    continue
                box = rest[0]
                if box.width < 2:
                    xs.add(middle_x(box))
                if box.height < 2:
                    ys.add(middle_y(box))
        return sorted(xs), sorted(ys)

    @cached_property
    def words(self):
        return [(pymupdf.Rect(w[:4]), w[4]) for w in self.page.get_text("words")]

    def write_at(self, left, baseline, text, right=None, align=pymupdf.TEXT_ALIGN_LEFT):
        if right is None:
            right = left + pymupdf.get_text_length(text, fontname="helv", fontsize=FONT_SIZE) + FONT_SIZE
        top = baseline - FIRST_BASELINE
        box = pymupdf.Rect(left, top, right, top + 1.5 * FONT_SIZE)
        self.page.add_freetext_annot(
            box, text, fontsize=FONT_SIZE, fontname="Helv", text_color=(0, 0, 0), align=align,
        )


class TableRow:
    def __init__(self, page, date_number):
        self.page = page
        xs, ys = page.ruling_lines
        header = page.find("TARIKH/")
        left, right = lines_around(xs, middle_x(header), "column 'TARIKH/'")
        numbers = [
            box for box, word in page.words
            if word == str(date_number) and left < middle_x(box) < right and box.y0 > header.y1
        ]
        if not numbers:
            raise FormLayoutError(f"No row for date {date_number} on page {page.number} of the form")
        self.top, self.bottom = lines_around(ys, middle_y(numbers[0]), f"row {date_number}")

    def write(self, column_header, text):
        xs, _ = self.page.ruling_lines
        header = self.page.find(column_header)
        left, right = lines_around(xs, middle_x(header), f"column '{column_header}'")
        baseline = (self.top + self.bottom) / 2 + CAP_HEIGHT / 2
        self.page.write_at(left, baseline, text, right=right, align=pymupdf.TEXT_ALIGN_CENTER)


def middle_x(box):
    return (box.x0 + box.x1) / 2


def middle_y(box):
    return (box.y0 + box.y1) / 2


def same_line(a, b):
    return abs(middle_y(a) - middle_y(b)) < b.height / 2


def lines_around(lines, position, what):
    before = [line for line in lines if line < position]
    after = [line for line in lines if line > position]
    if not before or not after:
        raise FormLayoutError(f"Couldn't find the table lines around {what}")
    return max(before), min(after)
