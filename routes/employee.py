from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    send_from_directory
)
from flask import current_app
from flask_login import current_user, login_required
from models.employee import Employee
from models.attendance import Attendance
from models.leave import Leave
from models.user import User
from models.shift import Shift
from extensions import db, bcrypt
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError
import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from models.document import Document
from extensions import db

employee = Blueprint("employee", __name__)


# ==========================
# Employee Dashboard
# ==========================
@employee.route("/employee/dashboard")
@login_required
def employee_dashboard():

    if not current_user.has_role("employee"):
        abort(403)

    employee_data = current_user.employee

    today_attendance = Attendance.query.filter_by(
        employee_id=employee_data.id,
        date=date.today()
    ).first()

    # Recompute late hours from the stored check-in time and the assigned shift
    if today_attendance and today_attendance.check_in:

        today_attendance.shift_id = employee_data.shift_id

        if employee_data.shift:
            today_attendance.shift_start = employee_data.shift.start_time
            today_attendance.shift_end = employee_data.shift.end_time

        if today_attendance.shift_start:

            check_in_dt = datetime.combine(date.today(), today_attendance.check_in)
            shift_start_dt = datetime.combine(date.today(), today_attendance.shift_start)

            late = (check_in_dt - shift_start_dt).total_seconds() / 3600

            today_attendance.late_hours = round(max(0, late), 2)

        db.session.commit()

    attendance_count = Attendance.query.filter_by(
        employee_id=employee_data.id
    ).count()

    leave_count = Leave.query.filter_by(
        employee_id=employee_data.id
    ).count()

    # Salary Calculation
    attendance_records = Attendance.query.filter_by(
        employee_id=employee_data.id
    ).all()

    total_overtime_hours = sum(
        record.overtime_hours or 0
        for record in attendance_records
    )

    total_overtime_pay = sum(
        record.overtime_pay or 0
        for record in attendance_records
    )

    # Hourly Rate Calculation
    working_days = 26
    hours_per_day = 8

    regular_hourly_rate = round(
        employee_data.basic_salary / (working_days * hours_per_day),
        2
    )

    overtime_hourly_rate = round(
        regular_hourly_rate * 1.05,
        2
    )

    # Total Salary
    total_salary = round(
        employee_data.basic_salary + total_overtime_pay,
        2
    )

    return render_template(
        "employee/dashboard.html",
        today_attendance=today_attendance,
        employee=employee_data,
        attendance_count=attendance_count,
        leave_count=leave_count,
        total_overtime_hours=total_overtime_hours,
        total_overtime_pay=total_overtime_pay,
        total_salary=total_salary,
        regular_hourly_rate=regular_hourly_rate,
        overtime_hourly_rate=overtime_hourly_rate
    )

@employee.route("/employee/attendance")
@login_required
def employee_attendance():

    if not current_user.has_role("employee"):
        abort(403)

    employee_data = current_user.employee

    attendance = Attendance.query.filter_by(
        employee_id=employee_data.id
    ).order_by(
        Attendance.date.desc()
    ).all()

    return render_template(
        "employee/attendance.html",
        attendance=attendance,
        employee=employee_data
    )

# ==========================
# Employee List (Admin Only)
# ==========================
@employee.route("/employees")
@login_required
def employees():

    if not current_user.has_role("Super Admin"):
      abort(403)
    

    all_employees = Employee.query.all()

    return render_template(
        "employees.html",
        employees=all_employees
    )

# ==========================
# Edit Employee (Admin Only)
# ==========================
@employee.route("/edit_employee/<int:id>", methods=["GET", "POST"])
@login_required
def edit_employee(id):

    if not current_user.has_role("Super Admin"):
       abort(403)
    employee = Employee.query.get_or_404(id)
    shifts = Shift.query.all()

    if request.method == "POST":

        employee.employee_code = request.form.get("employee_code")
        employee.shift_id = int(request.form.get("shift_id"))
        employee.full_name = request.form.get("full_name")
        employee.email = request.form.get("email")
        employee.phone = request.form.get("phone")
        employee.department = request.form.get("department")
        employee.designation = request.form.get("designation")

        # Joining Date
        joining_date_str = request.form.get("joining_date")

        if joining_date_str:
            employee.joining_date = datetime.strptime(
                joining_date_str,
                "%Y-%m-%d"
            ).date()

        # Resignation Date
        resignation_date_str = request.form.get("resignation_date")

        if resignation_date_str:
            employee.resignation_date = datetime.strptime(
                resignation_date_str,
                "%Y-%m-%d"
            ).date()
        else:
            employee.resignation_date = None

        # Employment
        employee.employment_type = request.form.get("employment_type")
        employee.location = request.form.get("location")

        # Salary
        employee.basic_salary = float(request.form.get("basic_salary"))
        employee.overtime_rate = float(request.form.get("overtime_rate"))

        # Status
        employee.status = request.form.get("status", "Active")

        # Emergency Contact
        employee.emergency_contact_name = request.form.get(
            "emergency_contact_name"
        )

        employee.emergency_contact_relation = request.form.get(
            "emergency_contact_relation"
        )

        employee.emergency_contact_phone = request.form.get(
            "emergency_contact_phone"
        )

        db.session.commit()

        flash("Employee updated successfully!", "success")

        return redirect(url_for("employee.employees"))

    return render_template(
        "edit_employee.html",
        employee=employee,
        shifts=shifts
    )


# ==========================
# Delete Employee (Admin Only)
# ==========================
@employee.route("/delete_employee/<int:id>")
@login_required
def delete_employee(id):

    if not current_user.has_role("Super Admin"):
       abort(403)


    employee = Employee.query.get_or_404(id)

    try:

        Attendance.query.filter_by(employee_id=id).delete()
        Leave.query.filter_by(employee_id=id).delete()
        User.query.filter_by(employee_id=id).delete()

        db.session.delete(employee)
        db.session.commit()

        flash("Employee and all related records deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for("employee.employees"))


# ==========================
# Add Employee (Admin Only)
# ==========================
@employee.route("/add_employee", methods=["GET", "POST"])
@login_required
def add_employee():

    if not current_user.has_role("Super Admin"):
      abort(403)
    shifts = Shift.query.all()

    if request.method == "POST":
        # ==========================
        # File Upload
        # ==========================

        profile_photo = request.files.get("profile_photo")
        cnic_file = request.files.get("cnic_file")
        cv_file = request.files.get("cv_file")
        certificate_file = request.files.get("certificate_file")

        profile_photo_name = None
        cnic_name = None
        cv_name = None
        certificate_name = None

        resignation_date = request.form.get("resignation_date")

        if resignation_date:
            resignation_date = datetime.strptime(
                resignation_date,
                "%Y-%m-%d"
            ).date()
        else:
            resignation_date = None

        new_employee = Employee(
            profile_photo=profile_photo_name,
            cnic_file=cnic_name,
            cv_file=cv_name,
            certificate_file=certificate_name,
            employee_code=request.form.get("employee_code"),
            full_name=request.form.get("full_name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            department=request.form.get("department"),
            designation=request.form.get("designation"),
            joining_date=datetime.strptime(
                request.form.get("joining_date"),
                "%Y-%m-%d"
            ).date(),
            resignation_date=resignation_date,
            basic_salary=float(request.form.get("basic_salary")),
            overtime_rate=float(request.form.get("overtime_rate")),
            shift_id=int(request.form.get("shift_id")),
            employment_type=request.form.get("employment_type"),
            location=request.form.get("location"),
            status=request.form.get("status", "Active"),
            emergency_contact_name=request.form.get("emergency_contact_name"),
            emergency_contact_relation=request.form.get("emergency_contact_relation"),
            emergency_contact_phone=request.form.get("emergency_contact_phone")
        )

        try:
            db.session.add(new_employee)
            db.session.commit()

            attendance = Attendance(
                employee_id=new_employee.id,
                status="Absent",
                check_in=None,
                check_out=None,
                shift_start=new_employee.shift.start_time if new_employee.shift else None,
                shift_end=new_employee.shift.end_time if new_employee.shift else None,
                working_hours=0,
                overtime_hours=0,
                overtime_pay=0,
                date=date.today()
            )

            db.session.add(attendance)

            hashed_password = bcrypt.generate_password_hash(
                "employee123"
            ).decode("utf-8")

            user = User(
                username=new_employee.email,
                email=new_employee.email,
                password=hashed_password,
                role="employee",
                employee_id=new_employee.id
            )

            db.session.add(user)
            db.session.commit()

            flash(
                "Employee added successfully! Default Password: employee123",
                "success"
            )

            return redirect(url_for("employee.employees"))

        except IntegrityError:
            db.session.rollback()
            flash(
                "Employee Code or Email already exists!",
                "danger"
            )

    return render_template(
        "add_employee.html",
        shifts=shifts
    )
@employee.route("/employee/today_attendance")
@login_required
def today_attendance():

    if not current_user.has_role("employee"):
        abort(403)

    employee_data = current_user.employee

    attendance = Attendance.query.filter_by(
        employee_id=employee_data.id,
        date=date.today()
    ).first()

    # Recompute late hours from the stored check-in time and the assigned shift
    # so it always reflects the correct value even if the shift was assigned
    # after the employee checked in.
    if attendance and attendance.check_in:

        attendance.shift_id = employee_data.shift_id

        if employee_data.shift:
            attendance.shift_start = employee_data.shift.start_time
            attendance.shift_end = employee_data.shift.end_time

        if attendance.shift_start:

            check_in_dt = datetime.combine(date.today(), attendance.check_in)
            shift_start_dt = datetime.combine(date.today(), attendance.shift_start)

            late = (check_in_dt - shift_start_dt).total_seconds() / 3600

            attendance.late_hours = round(max(0, late), 2)

        db.session.commit()

    return render_template(
        "employee/mark_attendance.html",
        employee=employee_data,
        attendance=attendance
    )
# ==========================
# Employee Mark Attendance
# ==========================
@employee.route("/employee/mark_attendance", methods=["POST"])
@login_required
def mark_attendance():

    if not current_user.has_role("employee"):
        abort(403)

    employee_data = current_user.employee
    action = request.form.get("action")

    attendance = Attendance.query.filter_by(
        employee_id=employee_data.id,
        date=date.today()
    ).first()

# ==========================
    # CHECK IN
    # ==========================
    if action == "check_in":

        already_checked_in = False

        # If a default "Absent" record exists (created at employee creation),
        # update it instead of blocking the employee from checking in.
        if attendance:

            if not attendance.check_in:
                # Update the existing default record instead of creating a new one
                attendance.status = "Present"
                attendance.check_in = datetime.now().time()
                attendance.shift_id = employee_data.shift_id
                attendance.shift_start = (
                    employee_data.shift.start_time
                    if employee_data.shift else attendance.shift_start
                )
                attendance.shift_end = (
                    employee_data.shift.end_time
                    if employee_data.shift else attendance.shift_end
                )
            else:
                # Already checked in - ensure shift timing is set so late hours
                # can still be recomputed from the stored check-in time.
                already_checked_in = True
                if attendance.shift_start is None and employee_data.shift:
                    attendance.shift_start = employee_data.shift.start_time
                    attendance.shift_end = employee_data.shift.end_time

        else:

            attendance = Attendance(
                employee_id=employee_data.id,
                shift_id=employee_data.shift_id,
                date=date.today(),
                status="Present",
                check_in=datetime.now().time(),
                shift_start=employee_data.shift.start_time if employee_data.shift else None,
                shift_end=employee_data.shift.end_time if employee_data.shift else None
            )
        # ==========================
        # LATE ARRIVAL
        # ==========================

        if attendance.shift_start and attendance.check_in:

            attendance_date = attendance.date or date.today()

            check_in_dt = datetime.combine(
                attendance_date,
                attendance.check_in
            )

            shift_start_dt = datetime.combine(
                attendance_date,
                attendance.shift_start
            )

            if check_in_dt > shift_start_dt:

                late_minutes = (
                    check_in_dt - shift_start_dt
                ).total_seconds() / 60

                attendance.late_hours = round(
                    late_minutes / 60,
                    2
                )

            else:

                attendance.late_hours = 0.0

        else:

            attendance.late_hours = 0.0

        db.session.add(attendance)
        db.session.commit()

        if already_checked_in:
            flash("You have already checked in today. Late hours updated.", "warning")
        else:
            flash("Check In Successful!", "success")

        return redirect(url_for("employee.today_attendance"))

    # ==========================
    # CHECK OUT
    # ==========================
    elif action == "check_out":

        if not attendance:
            flash("Please Check In first.", "danger")
            return redirect(url_for("employee.today_attendance"))

        if attendance.check_out:
            flash("Already Checked Out.", "warning")
            return redirect(url_for("employee.today_attendance"))

        attendance.check_out = datetime.now().time()

        check_in_dt = datetime.combine(date.today(), attendance.check_in)
        check_out_dt = datetime.combine(date.today(), attendance.check_out)

        # Overnight Shift
        if check_out_dt < check_in_dt:
            check_out_dt += timedelta(days=1)

        working_hours = round(
            (check_out_dt - check_in_dt).total_seconds() / 3600,
            2
        )

        attendance.working_hours = working_hours

        # ==========================
        # Early Leave
        # ==========================
        if attendance.shift_end:

            shift_end_dt = datetime.combine(
                date.today(),
                attendance.shift_end
            )

            if check_out_dt < shift_end_dt:

                attendance.early_leave_hours = round(
                    (shift_end_dt - check_out_dt).total_seconds() / 3600,
                    2
                )
            else:
                attendance.early_leave_hours = 0

        # ==========================
        # Overtime
        # ==========================
        standard_hours = (
            employee_data.shift.working_hours
            if employee_data.shift
            else 8
        )

        if working_hours > standard_hours:

            attendance.overtime_hours = round(
                working_hours - standard_hours,
                2
            )

            regular_hourly_rate = employee_data.basic_salary / (26 * 8)

            overtime_hourly_rate = regular_hourly_rate * 1.05

            attendance.overtime_pay = round(
                attendance.overtime_hours * overtime_hourly_rate,
                2
            )

        else:

            attendance.overtime_hours = 0
            attendance.overtime_pay = 0

        db.session.commit()

        flash("Check Out Successful!", "success")

        return redirect(url_for("employee.today_attendance"))

    flash("Invalid Request.", "danger")

    return redirect(url_for("employee.today_attendance"))
# =====================================
# Employee Documents
# =====================================

@employee.route("/employee/documents")
@login_required
def my_documents():

    employee = current_user.employee

    if not employee:
        abort(404)

    documents = Document.query.filter(
        db.or_(
            Document.employee_id == employee.id,
            Document.document_type == "Company Policy"
        )
    ).order_by(
        Document.uploaded_at.desc()
    ).all()

    return render_template(
        "employee/documents.html",
        documents=documents
    )

# =====================================
# Download Employee Document
# =====================================

@employee.route("/employee/documents/download/<int:id>")
@login_required
def download_document(id):

    employee = current_user.employee

    if not employee:
        abort(404)

    document = Document.query.get_or_404(id)

    # Employee apna document ya Company Policy download kar sakta hai
    if (
        document.employee_id != employee.id
        and document.document_type != "Company Policy"
    ):
        abort(403)

    from flask import send_from_directory

    directory = os.path.dirname(document.file_path)
    filename = os.path.basename(document.file_path)

    return send_from_directory(
        directory,
        filename,
        as_attachment=True
    )
@employee.route("/documents/view/<int:id>")
@login_required
def view_document(id):

    employee = current_user.employee

    if not employee:
        abort(404)

    document = Document.query.get_or_404(id)

    # Security check
    if (
        document.employee_id != employee.id
        and document.document_type != "Company Policy"
    ):
        abort(403)

    file_path = document.file_path

    if not os.path.exists(file_path):
        abort(404)

    # PDF ko browser mein open karna hai
    if document.file_name.lower().endswith(".pdf"):

        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            mimetype="application/pdf",
            as_attachment=False
        )

    # DOC/DOCX browser normally directly preview nahi karta
    abort(415)