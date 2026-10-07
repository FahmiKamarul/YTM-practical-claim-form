# Claim Form Filler

Fills in your monthly Yayasan TM claim form (BTEPV4): working days, Malay day names, times and hours. Set it up once, then it's one command a month.

## You need

- A computer (Windows, Mac or Linux)
- Python 3.11 or newer. Check by typing `python3 --version` in Terminal. If it shows a lower number (e.g. 3.9.6), install the latest from [python.org/downloads](https://www.python.org/downloads/).
- Your blank stamped form (PDF): page 1 signed and stamped, page 2 empty

**On Windows**, use PowerShell instead of Terminal, `python` instead of `python3`, and `.venv\Scripts\` instead of `.venv/bin/` everywhere below.

## Set up (once)

1. Open **Terminal**, type `cd ` (with a space), drag this folder into the window, and press Enter.
2. Run these one at a time:
   ```
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python fill_claim.py setup
   ```
3. Answer the questions:
   - Dates are year-month-day, e.g. `2026-08-10`.
   - For the form, drag the PDF into the Terminal window.
   - Press Enter to keep a value shown in `[brackets]`.
   - State is where you work, e.g. `SGR` (Selangor) or `KUL` (Kuala Lumpur).

Keep your stamped form where it is; the tool reads it every month. To change your details later, run setup again.

## Every month

Go to this folder in Terminal (step 1), then run it with the month you're claiming:
```
.venv/bin/python fill_claim.py 2026-11
```
The filled form is saved in your Downloads. Check it before you send it.

On leave, or worked on a public holiday? Add the days:
```
.venv/bin/python fill_claim.py 2026-11 --skip 12-13 --work 9
```
`--skip` is days off, `--work` is holidays you worked. For anything else (e.g. a half day), edit that cell in Preview or any PDF editor; every value is an editable text box.

## If it doesn't work

| You see | Do this |
|---|---|
| `no such file or directory: venv/bin/python` | Add the dot: `.venv/bin/python` |
| `no such file or directory: .venv/bin/python` | You're not in this folder, or skipped step 2. Redo step 1. |
| `No module named 'tomllib'` | Python is too old. Install 3.11+, run `rm -rf .venv`, then redo step 2. |
| `No file at ...` | Your form moved. Run setup again. |
| `... already exists` | That month is already in Downloads. Delete the old file first. |

Any other message explains what's wrong.
