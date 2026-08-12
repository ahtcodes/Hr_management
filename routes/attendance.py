from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from models.attendance import Attendance
from models.employee import Employee
from extensions import db
from datetime import datetime, date

attendance = Blueprint("attendance", __name__)


# =========================
# Attendance List
# =========================
@attendance.route("/attendance")
@login_required
def attendance_list():

    records = Attendance.query.all()

    return render_template(
        "attendance.html",
        records=records
    )

# =========================
# Mark Attendance
# =========================

@attendance.route("/mark_attendance", methods=["GET", "POST"])
@login_required
def mark_attendance():

    if not current_user.has_role("Super Admin"):
        abort(403)

    employees = Employee.query.all()

    if request.method == "POST":

        employee_id = request.form.get("employee_id")
        status = request.form.get("status")
        check_in_str = request.form.get("check_in")
        check_out_str = request.form.get("check_out")

        check_in = (
            datetime.strptime(check_in_str, "%H:%M").time()
            if check_in_str else None
        )

        check_out = (
            datetime.strptime(check_out_str, "%H:%M").time()
            if check_out_str else None
        )

        attendance_record = Attendance(
            employee_id=int(employee_id),
            date=date.today(),
            status=status,
            check_in=check_in,
            check_out=check_out,
            working_hours=0,
            overtime_hours=0,
            overtime_pay=0
        )

        db.session.add(attendance_record)
        db.session.commit()

        flash("Attendance marked successfully!", "success")

        return redirect(url_for("attendance.attendance_list"))

    return render_template(
        "mark_attendance.html",
        employees=employees
    )




# =========================
# Edit Attendance (Admin Only)
# =========================
@attendance.route("/edit_attendance/<int:id>", methods=["GET", "POST"])
@login_required
def edit_attendance(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    record = Attendance.query.get_or_404(id)

    if request.method == "POST":

        check_in_str = request.form.get("check_in")
        check_out_str = request.form.get("check_out")

        check_in = datetime.strptime(
            check_in_str,
            "%H:%M"
        ).time() if check_in_str else None

        check_out = datetime.strptime(
            check_out_str,
            "%H:%M"
        ).time() if check_out_str else None

        status = request.form.get("status")

        working_hours = 0
        overtime_hours = 0
        overtime_pay = 0

        if status == "Present" and check_in and check_out:

            in_minutes = check_in.hour * 60 + check_in.minute
            out_minutes = check_out.hour * 60 + check_out.minute

            diff_minutes = out_minutes - in_minutes

            if diff_minutes < 0:
                diff_minutes += 24 * 60

            working_hours = round(diff_minutes / 60, 1)

            standard_hours = current_app.config.get(
                "STANDARD_WORK_HOURS",
                8
            )

            if working_hours > standard_hours:

                overtime_hours = round(
                    working_hours - standard_hours,
                    1
                )

                employee_record = Employee.query.get(
                    int(request.form.get("employee_id"))
                )

            if employee_record:

                working_days = 26
                hours_per_day = 8

    # Monthly salary se hourly rate
                regular_hourly_rate = employee_record.basic_salary / (
                working_days * hours_per_day
                )   

    # 5% extra overtime rate
                overtime_hourly_rate = regular_hourly_rate * 1.05

    # Overtime pay
                overtime_pay = round(
                overtime_hours * overtime_hourly_rate,
                2
                )

        record.employee_id = int(request.form.get("employee_id"))
        record.status = status
        record.check_in = check_in
        record.check_out = check_out

        emp = Employee.query.get(record.employee_id)
        record.shift_start = emp.shift.start_time if emp and emp.shift else record.shift_start
        record.shift_end = emp.shift.end_time if emp and emp.shift else record.shift_end

        record.working_hours = working_hours
        record.overtime_hours = overtime_hours
        record.overtime_pay = overtime_pay

        db.session.commit()

        flash("Attendance updated successfully!", "success")

        return redirect(url_for("attendance.attendance_list"))

    employees = Employee.query.all()

    return render_template(
        "edit_attendance.html",
        record=record,
        employees=employees
    )


# =========================
# Delete Attendance (Admin Only)
# =========================
@attendance.route("/delete_attendance/<int:id>")
@login_required
def delete_attendance(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    record = Attendance.query.get_or_404(id)

    db.session.delete(record)
    db.session.commit()

    flash("Attendance record deleted!", "info")

    return redirect(url_for("attendance.attendance_list"))

