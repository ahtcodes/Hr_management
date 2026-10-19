from flask import Blueprint, render_template, request, redirect, url_for, flash, abort,send_file
from flask_login import login_required, current_user
from models.payroll import Payroll
from models.employee import Employee
from extensions import db
from models.attendance import Attendance
from models.leave import Leave
from datetime import datetime, date, timedelta
import json

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)



payroll = Blueprint(
    "payroll",
    __name__,
    url_prefix="/payroll"
)


# Payroll List
@payroll.route("", methods=["GET"])
@login_required
def payroll_list():

    # Delete Payroll
    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    payrolls = Payroll.query.order_by(
        Payroll.year.desc(),
        Payroll.created_at.desc()
    ).all()

    return render_template(
        "payroll/payrolls.html",
        payrolls=payrolls
    )





# ==========================
# Salary History
# ==========================

@payroll.route("/history", methods=["GET"])
@login_required
def salary_history():

    # ==========================================
    # Super Admin
    # ==========================================
    #
    # Super Admin -> all salary records
    #
    # ==========================================

    if current_user.has_any_role("Super Admin", "HR Manager"):

        payrolls = Payroll.query.order_by(
            Payroll.year.desc(),
            Payroll.created_at.desc()
        ).all()

    # ==========================================
    # Employee
    # ==========================================
    #
    # Employee -> only his/her own salary records
    #
    # ==========================================

    else:

        employee = current_user.employee

        if not employee:
            abort(404)

        payrolls = Payroll.query.filter_by(
            employee_id=employee.id
        ).order_by(
            Payroll.year.desc(),
            Payroll.created_at.desc()
        ).all()

    return render_template(
        "payroll/history.html",
        payrolls=payrolls
    )


# ==========================
# Generate Payroll
# ==========================

@payroll.route("/generate", methods=["GET", "POST"])
@login_required
def generate_payroll():

    # Only Super Admin
    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    employees = Employee.query.all()

    if request.method == "POST":

        # ==========================
        # Form Data
        # ==========================

        employee_id = int(request.form.get("employee_id"))
        month = request.form.get("month")
        year = int(request.form.get("year"))

        employee = Employee.query.get_or_404(employee_id)

        basic_salary = float(employee.basic_salary or 0)

        allowances = float(
            request.form.get("allowances") or 0
        )

        bonus = float(
            request.form.get("bonus") or 0
        )

        tax = float(
            request.form.get("tax") or 0
        )

        # 5% Security deduction
        security_deduction = round(
            basic_salary * 0.05,
            2
        )

        # ==========================
        # Convert Month
        # ==========================

        try:
            month_number = datetime.strptime(
                month,
                "%B"
            ).month

        except ValueError:

            try:
                month_number = datetime.strptime(
                    month,
                    "%b"
                ).month

            except ValueError:
                month_number = int(month)

        # ==========================
        # Selected Month Dates
        # ==========================

        month_start = date(
            year,
            month_number,
            1
        )

        if month_number == 12:

            month_end = date(
                year + 1,
                1,
                1
            ) - timedelta(days=1)

        else:

            month_end = date(
                year,
                month_number + 1,
                1
            ) - timedelta(days=1)

        # ==========================
        # IMPORTANT:
        # Payroll only up to TODAY
        # ==========================

        today = date.today()

        payroll_end = min(
            month_end,
            today
        )

        # ==========================
        # Standard Working Hours
        # ==========================

        standard_hours_per_day = (
            employee.shift.working_hours
            if employee.shift
            and employee.shift.working_hours
            else 8
        )

        # ==========================
        # Payroll Start Date
        # ==========================
        #
        # Start from employee joining date.
        #
        # If attendance exists later than joining date,
        # attendance will still be used for actual presence.
        #
        # Future dates are never included.
        # ==========================

        employee_join = (
            employee.joining_date
            if employee.joining_date
            else month_start
        )

        eligible_start = max(
            month_start,
            employee_join
        )

        # Safety check
        if eligible_start > payroll_end:

            working_days = 0
            daily_rate = 0
            hourly_rate = 0

            breakdown = []

            present_days = 0
            absent_days = 0
            leave_days = 0

            total_regular_hours = 0
            total_overtime_hours = 0

        else:

            # ==========================
            # Working Days
            # Monday-Friday
            # ==========================

            working_days = 0

            d = eligible_start

            while d <= payroll_end:

                if d.weekday() < 5:
                    working_days += 1

                d += timedelta(days=1)

            # ==========================
            # Daily Rate
            # ==========================

            daily_rate = (
                basic_salary / working_days
                if basic_salary > 0
                and working_days > 0
                else 0
            )

            # ==========================
            # Hourly Rate
            # ==========================

            hourly_rate = (
                daily_rate / standard_hours_per_day
                if daily_rate > 0
                and standard_hours_per_day > 0
                else 0
            )

            # ==========================
            # Attendance
            # ==========================

            attendance_records = Attendance.query.filter(
                Attendance.employee_id == employee_id,
                Attendance.date >= eligible_start,
                Attendance.date <= payroll_end
            ).all()

            present_days = 0
            absent_days = 0
            leave_days = 0

            total_regular_hours = 0
            total_overtime_hours = 0

            late_count = 0
            early_leave_count = 0

            # ==========================
            # Approved Leaves
            # ==========================

            approved_leaves = Leave.query.filter(
                Leave.employee_id == employee_id,
                Leave.status.in_(
                    ["Approved", "approved"]
                )
            ).all()

            leave_date_set = set()

            for lv in approved_leaves:

                if lv.start_date and lv.end_date:

                    cur = lv.start_date

                    while cur <= lv.end_date:

                        # Only selected payroll period
                        if (
                            eligible_start
                            <= cur
                            <= payroll_end
                        ):
                            leave_date_set.add(cur)

                        cur += timedelta(days=1)

            # ==========================
            # Attendance Map
            # ==========================

            att_by_date = {}

            for attendance in attendance_records:

                if attendance.date is None:
                    continue

                att_by_date[
                    attendance.date
                ] = attendance

            # ==========================
            # Daily Breakdown
            # ==========================

            breakdown = []

            d = eligible_start

            while d <= payroll_end:

                # Saturday / Sunday ignored
                if d.weekday() >= 5:

                    d += timedelta(days=1)
                    continue

                attendance = att_by_date.get(d)

                day_status = "Absent"

                check_in = None
                check_out = None

                day_working_hours = 0
                day_regular_hours = 0
                day_late_hours = 0
                day_early_leave = 0
                day_overtime = 0

                day_leave_type = None

                # ==========================
                # APPROVED LEAVE
                # ==========================

                if d in leave_date_set:

                    day_status = "On Leave"

                    leave_days += 1

                # ==========================
                # PRESENT
                # ==========================

                elif (
                    attendance is not None
                    and attendance.status == "Present"
                ):

                    day_status = "Present"

                    present_days += 1

                    check_in = attendance.check_in
                    check_out = attendance.check_out

                    day_working_hours = (
                        attendance.working_hours or 0
                    )

                    day_late_hours = (
                        attendance.late_hours or 0
                    )

                    day_early_leave = (
                        attendance.early_leave_hours or 0
                    )

                    day_overtime = (
                        attendance.overtime_hours or 0
                    )

                    # Regular hours exclude overtime
                    day_regular_hours = max(
                        0,
                        day_working_hours
                        - day_overtime
                    )

                    total_regular_hours += (
                        day_regular_hours
                    )

                    total_overtime_hours += (
                        day_overtime
                    )

                    if day_late_hours > 0:
                        late_count += 1

                    if day_early_leave > 0:
                        early_leave_count += 1

                # ==========================
                # ATTENDANCE STATUS = LEAVE
                # ==========================

                elif (
                    attendance is not None
                    and attendance.status == "Leave"
                ):

                    day_status = "On Leave"

                    leave_days += 1

                # ==========================
                # ABSENT
                # ==========================

                else:

                    day_status = "Absent"

                    absent_days += 1

                # ==========================
                # Format Check In / Out
                # ==========================

                check_in_str = (
                    check_in.strftime("%I:%M %p")
                    if check_in
                    else None
                )

                check_out_str = (
                    check_out.strftime("%I:%M %p")
                    if check_out
                    else None
                )

                # ==========================
                # Daily Breakdown
                # ==========================

                breakdown.append({

                    "date": d.strftime(
                        "%Y-%m-%d"
                    ),

                    "day": d.strftime(
                        "%A"
                    ),

                    "status": day_status,

                    "leave_type": day_leave_type,

                    "check_in": check_in_str,

                    "check_out": check_out_str,

                    "working_hours": round(
                        day_regular_hours,
                        2
                    ),

                    "late_hours": round(
                        day_late_hours,
                        2
                    ),

                    "early_leave_hours": round(
                        day_early_leave,
                        2
                    ),

                    "overtime_hours": round(
                        day_overtime,
                        2
                    )
                })

                d += timedelta(days=1)

        # ==================================================
        # SALARY CALCULATION
        # ==================================================

        # ==========================
        # Basic Earned
        # ==========================
        #
        # Salary is based on actual
        # regular working hours.
        # ==========================

        basic_earned = round(
            total_regular_hours * hourly_rate,
            2
        )

        # ==========================
        # Overtime Pay
        # ==========================

        overtime_rate = (
            hourly_rate * 1.05
        )

        overtime_pay = round(
            total_overtime_hours
            * overtime_rate,
            2
        )

        # ==========================
        # Late Deduction
        # ==========================
        #
        # Exact late hours/minutes
        # are deducted.
        # ==========================

        total_late_hours = sum(
            item["late_hours"]
            for item in breakdown
            if item["status"] == "Present"
        )

        late_deduction = round(
            total_late_hours
            * hourly_rate,
            2
        )

        # ==========================
        # Early Leave Deduction
        # ==========================

        total_early_hours = sum(
            item["early_leave_hours"]
            for item in breakdown
            if item["status"] == "Present"
        )

        early_leave_deduction = round(
            total_early_hours
            * hourly_rate,
            2
        )

        # ==========================
        # Absence Deduction
        # ==========================
        #
        # Only absent days are deducted.
        # Approved leave is NOT deducted.
        # ==========================

        absence_deduction = round(
            absent_days
            * daily_rate,
            2
        )

        # ==========================
        # Gross Salary
        # ==========================

        gross_salary = round(
            basic_earned
            + allowances
            + overtime_pay
            + bonus,
            2
        )

        # ==========================
        # Total Deductions
        # ==========================

        total_deductions = round(

            late_deduction

            + early_leave_deduction

            + absence_deduction

            + tax

            + security_deduction,

            2
        )

        # ==========================
        # Net Salary
        # ==========================

        net_salary = round(
            gross_salary
            - total_deductions,
            2
        )

        # Salary cannot be negative
        final_salary = max(
            net_salary,
            0
        )

        # ==========================
        # Total Working Hours
        # ==========================

        total_working_hours = (
            total_regular_hours
            + total_overtime_hours
        )

        # ==========================
        # Create Payroll
        # ==========================

        new_payroll = Payroll(

            employee_id=employee_id,

            month=month,

            year=year,

            basic_salary=basic_salary,

            present_days=present_days,

            absent_days=absent_days,

            leave_days=leave_days,

            overtime_hours=round(
                total_overtime_hours,
                2
            ),

            overtime_pay=round(
                overtime_pay,
                2
            ),

            allowances=round(
                allowances,
                2
            ),

            bonus=round(
                bonus,
                2
            ),

            tax=round(
                tax,
                2
            ),

            security_deduction=round(
                security_deduction,
                2
            ),

            late_deduction=round(
                late_deduction
                + early_leave_deduction,
                2
            ),

            absence_deduction=round(
                absence_deduction,
                2
            ),

            deductions=round(
                total_deductions,
                2
            ),

            net_salary=round(
                net_salary,
                2
            ),

            final_salary=round(
                final_salary,
                2
            ),

            total_working_hours=round(
                total_regular_hours,
                2
            ),

            hourly_rate=round(
                hourly_rate,
                2
            ),

            daily_rate=round(
                daily_rate,
                2
            ),

            working_days=working_days,

            daily_breakdown=json.dumps(
                breakdown
            ),

            status="Pending"
        )

        db.session.add(
            new_payroll
        )

        db.session.commit()

        flash(
            f"Payroll generated automatically for "
            f"{employee.full_name} "
            f"(Present days: {present_days}, "
            f"Absent days: {absent_days}, "
            f"Leave days: {leave_days})",
            "success"
        )

        return redirect(
            url_for(
                "payroll.view_payroll",
                id=new_payroll.id
            )
        )

    return render_template(
        "payroll/generate.html",
        employees=employees,
        now_year=date.today().year
    )

# ==================================================
# View Payroll
# ==================================================

@payroll.route("/view/<int:id>")
@login_required
def view_payroll(id):

    payroll_data = Payroll.query.get_or_404(id)

    # ==================================================
    # Super Admin
    # ==================================================

    if current_user.has_any_role("Super Admin", "HR Manager"):

        # Super Admin can view any payroll
        pass

    # ==================================================
    # Employee
    # ==================================================

    else:

        # Current logged-in user's employee
        employee = Employee.query.filter_by(
            user=current_user
        ).first()

        if not employee:
            abort(403)

        # Employee can ONLY view own payroll
        if payroll_data.employee_id != employee.id:
            abort(403)

    # ==================================================
    # Parse Daily Breakdown
    # ==================================================

    try:

        breakdown = json.loads(
            payroll_data.daily_breakdown or "[]"
        )

    except Exception:

        breakdown = []

    # ==================================================
    # Attendance Summary
    # ==================================================

    summary = {

        "present": sum(
            1
            for b in breakdown
            if b.get("status") == "Present"
        ),

        "late": sum(
            1
            for b in breakdown
            if b.get("late_hours", 0) > 0
        ),

        "early_leave": sum(
            1
            for b in breakdown
            if b.get("early_leave_hours", 0) > 0
        ),

        "on_time": sum(
            1
            for b in breakdown
            if (
                b.get("status") == "Present"
                and b.get("late_hours", 0) == 0
            )
        ),

        "leave": sum(
            1
            for b in breakdown
            if b.get("status") == "On Leave"
        ),

        "absent": sum(
            1
            for b in breakdown
            if b.get("status") == "Absent"
        )
    }

    # ==================================================
    # View
    # ==================================================

    return render_template(
        "payroll/view.html",
        payroll=payroll_data,
        breakdown=breakdown,
        summary=summary
    )



# Delete Payroll
@payroll.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_payroll(id):

   # Delete Payroll
    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    payroll_data = Payroll.query.get_or_404(id)

    db.session.delete(payroll_data)
    db.session.commit()

    flash("Payroll record deleted successfully!", "success")

    return redirect(url_for("payroll.payroll_list"))

# ==========================
# Payslip PDF
# ==========================

@payroll.route("/payslip/<int:payroll_id>")
@login_required
def payslip(payroll_id):

    payroll_record = Payroll.query.get_or_404(payroll_id)

    # ==========================
    # Permission Check
    # ==========================

    # Super Admin can download any payslip
    if current_user.has_any_role("Super Admin"):
        pass

    else:
        # Employee must be linked to an employee record
        if not current_user.employee_id:
            abort(403)

        # Employee can download ONLY own payslip
        if payroll_record.employee_id != current_user.employee_id:
            abort(403)

    employee = payroll_record.employee

    if not employee:
        abort(404)

    # ==========================
    # Create PDF
    # ==========================

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    # ==========================
    # Header
    # ==========================

    pdf.setFont("Helvetica-Bold", 20)

    pdf.drawString(
        50,
        height - 60,
        "PEOPLEDESK HR"
    )

    pdf.setFont("Helvetica-Bold", 16)

    pdf.drawString(
        50,
        height - 95,
        "EMPLOYEE PAYSLIP"
    )

    pdf.setFont("Helvetica", 10)

    pdf.drawRightString(
        width - 50,
        height - 60,
        f"Payroll ID: {payroll_record.id}"
    )

    # ==========================
    # Employee Information
    # ==========================

    y = height - 140

    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        50,
        y,
        "Employee Information"
    )

    y -= 25

    pdf.setFont("Helvetica", 10)

    employee_name = employee.full_name or "N/A"

    pdf.drawString(
        50,
        y,
        f"Employee: {employee_name}"
    )

    pdf.drawString(
        300,
        y,
        f"Employee ID: {employee.id}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Employee Code: {employee.employee_code or 'N/A'}"
    )

    pdf.drawString(
        300,
        y,
        f"Department: {employee.department or 'N/A'}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Payroll Month: {payroll_record.month} {payroll_record.year}"
    )

    pdf.drawString(
        300,
        y,
        f"Status: {payroll_record.status}"
    )

    # ==========================
    # Attendance Summary
    # ==========================

    y -= 40

    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        50,
        y,
        "Attendance Summary"
    )

    y -= 25

    pdf.setFont("Helvetica", 10)

    attendance_data = [
        ("Working Days", payroll_record.working_days),
        ("Present Days", payroll_record.present_days),
        ("Absent Days", payroll_record.absent_days),
        ("Leave Days", payroll_record.leave_days),
        ("Working Hours", payroll_record.total_working_hours),
        ("Overtime Hours", payroll_record.overtime_hours),
    ]

    for label, value in attendance_data:

        pdf.drawString(
            60,
            y,
            str(label)
        )

        pdf.drawRightString(
            250,
            y,
            str(value or 0)
        )

        y -= 18

    # ==========================
    # Salary Details
    # ==========================

    y -= 15

    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        50,
        y,
        "Salary Details"
    )

    y -= 25

    pdf.setFont("Helvetica", 10)

    salary_data = [
        ("Basic Salary", payroll_record.basic_salary),
        ("Allowances", payroll_record.allowances),
        ("Overtime Pay", payroll_record.overtime_pay),
        ("Bonus", payroll_record.bonus),
        ("Late Deduction", payroll_record.late_deduction),
        ("Absence Deduction", payroll_record.absence_deduction),
        ("Other Deductions", payroll_record.deductions),
        ("Tax", payroll_record.tax),
        ("5% Security Deduction", payroll_record.security_deduction),
    ]

    for label, value in salary_data:

        pdf.drawString(
            60,
            y,
            label
        )

        pdf.drawRightString(
            250,
            y,
            f"Rs. {float(value or 0):,.2f}"
        )

        y -= 18

    # ==========================
    # Final Salary
    # ==========================

    y -= 15

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    final_salary = (
        payroll_record.final_salary
        if payroll_record.final_salary
        else payroll_record.net_salary
    )

    pdf.drawString(
        50,
        y,
        "FINAL NET SALARY"
    )

    pdf.drawRightString(
        250,
        y,
        f"Rs. {float(final_salary or 0):,.2f}"
    )

    # ==========================
    # Footer
    # ==========================

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        50,
        40,
        "Generated by PeopleDesk HR Management System"
    )

    pdf.drawRightString(
        width - 50,
        40,
        datetime.now().strftime("%d-%m-%Y")
    )

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=(
            f"Payslip_{employee_name}_"
            f"{payroll_record.month}_"
            f"{payroll_record.year}.pdf"
        ),
        mimetype="application/pdf"
    )
