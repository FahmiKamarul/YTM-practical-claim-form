from claim.form import ClaimForm
from claim.workdays import long_date, malay_day_name


def fill_month(config, out, year, month, days, sign_date):
    form = ClaimForm(config.form_path)
    claim, timesheet = form.page(1), form.page(2)
    signed = long_date(sign_date)

    claim.write_on_line_below("No of working days", str(len(days)))
    claim.write_after("Tarikh / Date", signed, below="Pengakuan Pelajar")
    claim.write_after("Tarikh / Date", signed, below="Pengesahan Penyelia")

    timesheet.write_after("Name", config.name)
    timesheet.write_after("Year", str(year))
    timesheet.write_after("Month", str(month))
    for day in days:
        row = timesheet.table_row(day.day)
        row.write("HARI / DAY", malay_day_name(day))
        row.write("TIME IN", config.time_in)
        row.write("KELUAR", config.time_out)
        row.write("TOTAL HOURS", config.hours)

    form.save(out)
