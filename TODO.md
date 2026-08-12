# TODO — Payroll System Enhancement

## Context
- Salary calculated per-day (daily_rate × present working days Mon-Fri)
- Working days = Mon-Fri only
- Overtime not double-counted
- Add daily_rate column + delete button
- Prorate salary based on employee joining date (mid-month joins)

## Steps
- [x] 1. Fix `models/payroll.py` indentation (hourly_rate, daily_rate)
- [x] 2. Add `daily_rate` column to model + DB (verified present in DB)
- [x] 3. Rewrite `routes/payroll.py` — per-day salary calc, overtime not double-counted, delete route
- [x] 4. Add delete button to `templates/payroll/view.html` and `templates/payroll/payrolls.html`
- [x] 5. Update `templates/payroll/view.html` to show Daily Rate + Basic Earned per-day
- [x] 6. Prorate salary based on joining_date (working days & attendance counted from joining date onward)
- [x] 7. Verify app imports, route registered, model matches DB
</content>
