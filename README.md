# Claim Form Filler

Fills in your monthly Yayasan TM claim form (BTEPV4): working days, Malay day names, times and hours. Set it up once, then it's one command a month.

## You need

- A computer (Windows, Mac or Linux)
- Python 3.11 or newer, from [python.org/downloads](https://www.python.org/downloads/). Check your version:
  - **Mac/Linux:** type `python3 --version` in Terminal.
  - **Windows:** type `py --version` in PowerShell. When installing, tick **"Add python.exe to PATH"**.
- Your blank stamped form (PDF): page 1 signed and stamped, page 2 empty

If the version shown is lower than 3.11 (e.g. 3.9.6), install the latest.

## Set up (once)

1. Open **Terminal** (Mac/Linux) or **PowerShell** (Windows), type `cd ` (with a space), drag this folder into the window, and press Enter.
2. Run these one at a time:

   **Mac/Linux**
   ```
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python fill_claim.py setup
   ```

   **Windows**
   ```
   py -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   .venv\Scripts\python fill_claim.py setup
   ```
3. Answer the questions:
   - Dates are year-month-day, e.g. `2026-08-10`.
   - For the form, drag the PDF into the window.
   - Press Enter to keep a value shown in `[brackets]`.
   - State is where you work, e.g. `SGR` (Selangor) or `KUL` (Kuala Lumpur).

Keep your stamped form where it is; the tool reads it every month. To change your details later, run setup again.

## Every month

Go to this folder (step 1), then run it with the month you're claiming:

**Mac/Linux**
```
.venv/bin/python fill_claim.py 2026-11
```

**Windows**
```
.venv\Scripts\python fill_claim.py 2026-11
```

The filled form is saved in your Downloads. Check it before you send it.

On leave, or worked on a public holiday? Add the days (on Windows, start with `.venv\Scripts\python` instead):
```
.venv/bin/python fill_claim.py 2026-11 --skip 12-13 --work 9
```
`--skip` is days off, `--work` is holidays you worked. For anything else (e.g. a half day), edit that cell in Preview, Edge or any PDF editor; every value is an editable text box.

## If it doesn't work

| You see | Do this |
|---|---|
| `Python was not found; run without arguments to install from the Microsoft Store` | You're on Windows: use `py` instead of `python3`. |
| `'.venv/bin/pip' is not recognized` | You're on Windows: use `.venv\Scripts\` instead of `.venv/bin/`. |
| `'py' is not recognized` | Python isn't installed. Install it from python.org, then open a new PowerShell window. |
| `no such file or directory: venv/bin/python` | Add the dot: `.venv/bin/python` |
| `no such file or directory: .venv/bin/python` or `.venv\Scripts\python is not recognized` | You're not in this folder, or skipped step 2. Redo step 1. |
| `No module named 'tomllib'` | Python is too old. Install 3.11+, delete the `.venv` folder, then redo step 2. |
| `No file at ...` | Your form moved. Run setup again. |
| `... already exists` | That month is already in Downloads. Delete the old file first. |

Any other message explains what's wrong.
