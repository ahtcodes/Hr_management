from flask import Blueprint, render_template, request, abort, redirect, flash, url_for
from flask_login import login_required, current_user
from models.employee import Employee
from models.attendance import Attendance
from models.shift import Shift
from models.user import User
from models.activity_log import ActivityLog
from extensions import db
from models.login_history import LoginHistory
from models.role import Role
from datetime import datetime, date, timedelta
from models.document import Document
import os
from werkzeug.utils import secure_filename

admin = Blueprint("admin", __name__)
# ==========================
# Live Attendance
# ==========================
@admin.route("/live_attendance")
@login_required
def live_attendance():

    if not current_user.has_role("Super Admin"):
        abort(403)

    today = date.today()

    records = Attendance.query.filter_by(
        date=today
    ).join(Employee).all()

    return render_template(
        "admin/live_attendance.html",
        records=records
    )
# ==========================
# Biometric Integration Demo
# ==========================

@admin.route("/admin/biometric")
@login_required
def biometric():

    if not current_user.has_role("Super Admin"):
        abort(403)

    return render_template(
        "admin/biometric.html"
    )
# ==========================
# Demo Biometric Sync
# ==========================

@admin.route("/admin/biometric/sync", methods=["POST"])
@login_required
def biometric_sync():

    if not current_user.has_role("Super Admin"):
        abort(403)

    # Demo biometric ID
    biometric_id = "BIO-001"

    # Employee find karo
    employee = Employee.query.filter_by(
        biometric_id=biometric_id
    ).first()

    if not employee:
        flash("Biometric employee not found.", "danger")
        return redirect(url_for("admin.biometric"))

    today = date.today()

    # Aaj ki attendance check karo
    attendance = Attendance.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()

    # Agar attendance nahi hai to check-in create karo
    if not attendance:

        attendance = Attendance(
            employee_id=employee.id,
            date=today,
            status="Present",
            check_in=datetime.now().time(),
            shift_id=employee.shift_id,
            shift_start=(
                employee.shift.start_time
                if employee.shift else None
            ),
            shift_end=(
                employee.shift.end_time
                if employee.shift else None
            )
        )

        db.session.add(attendance)

    # Agar attendance hai aur check-in nahi hai
    elif not attendance.check_in:

        attendance.status = "Present"
        attendance.check_in = datetime.now().time()

    else:
        flash(
            f"{employee.full_name} is already checked in.",
            "warning"
        )
        return redirect(url_for("admin.biometric"))

    # Late Arrival calculate
    if attendance.shift_start and attendance.check_in:

        check_in_dt = datetime.combine(
            today,
            attendance.check_in
        )

        shift_start_dt = datetime.combine(
            today,
            attendance.shift_start
        )

        late = (
            check_in_dt - shift_start_dt
        ).total_seconds() / 3600

        attendance.late_hours = round(
            max(0, late),
            2
        )

    db.session.commit()

    flash(
        f"Biometric sync successful for {employee.full_name}.",
        "success"
    )

    return redirect(url_for("admin.biometric"))

# ==========================
# Attendance Reports
# ==========================

@admin.route("/admin/attendance_reports")
@login_required
def attendance_reports():

    if not current_user.has_role("Super Admin"):
        abort(403)

    # Filters
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    employee_id = request.args.get("employee_id")

    query = Attendance.query.join(Employee)

    # From Date
    if from_date:
        try:
            from_date_obj = datetime.strptime(
                from_date,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                Attendance.date >= from_date_obj
            )
        except ValueError:
            pass

    # To Date
    if to_date:
        try:
            to_date_obj = datetime.strptime(
                to_date,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                Attendance.date <= to_date_obj
            )
        except ValueError:
            pass

    # Employee Filter
    if employee_id:
        try:
            query = query.filter(
                Attendance.employee_id == int(employee_id)
            )
        except ValueError:
            pass

    records = query.order_by(
        Attendance.date.desc(),
        Attendance.id.desc()
    ).all()

    employees = Employee.query.order_by(
        Employee.full_name.asc()
    ).all()

    return render_template(
        "admin/attendance_reports.html",
        records=records,
        employees=employees,
        from_date=from_date,
        to_date=to_date,
        selected_employee=employee_id
    )

# =====================================
# Admin Dashboard
# =====================================

@admin.route("/admin/dashboard")
@login_required
def dashboard():

    if not current_user.has_role("Super Admin"):
        abort(403)

    total_employees = Employee.query.count()

    today = date.today()

    today_records = Attendance.query.join(Employee).filter(
        Attendance.date == today
    ).all()

    today_present = Attendance.query.filter(
        Attendance.date == today,
        Attendance.status == "Present",
        Attendance.check_in.isnot(None)
    ).count()

    on_leave = Attendance.query.filter(
        Attendance.date == today,
        Attendance.status == "Leave"
    ).count()

    absent_today = Attendance.query.filter(
        Attendance.date == today,
        Attendance.status == "Absent"
    ).count()

    remaining_absent = total_employees - (
        today_present + on_leave + absent_today
    )

    if remaining_absent > 0:
        absent_today += remaining_absent

    recent_employees = Employee.query.order_by(
        Employee.id.desc()
    ).limit(5).all()

    # Employee role se pending users
    pending_users = User.query.filter(
        User.role.has(name="Employee"),
        User.status == "pending"
    ).all()

    return render_template(
        "admin/dashboard.html",
        total_employees=total_employees,
        today_present=today_present,
        on_leave=on_leave,
        absent_today=absent_today,
        recent_employees=recent_employees,
        pending_users=pending_users,
        pending_requests=len(pending_users),
        today_records=today_records,
        today=datetime.now()
    )


# =====================================
# Pending Employee Requests
# =====================================
@admin.route("/admin/pending_users")
@login_required
def pending_users():

    if not current_user.has_role("Super Admin"):
        abort(403)

    users = User.query.filter_by(
        role="employee",
        status="pending"
    ).all()

    return render_template(
        "admin/pending_users.html",
        users=users
    )


# =====================================
# Approve Employee
# =====================================
@admin.route("/admin/approve/<int:user_id>")
@login_required
def approve_user(user_id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    user = User.query.get_or_404(user_id)

    # Approve account
    user.status = "approved"

    # Employee profile agar nahi hai to create karo
    if user.employee is None:

        # Check email se pehle employee maujood hai ya nahi
        employee = Employee.query.filter_by(email=user.email).first()

        if employee:
            user.employee_id = employee.id

        else:
            employee = Employee(
                employee_code=f"EMP{user.id:04}",
                full_name=user.username,
                email=user.email,
                phone="Not Added",
                department="Not Assigned",
                designation="Employee",
                joining_date=date.today(),
                basic_salary=0,
                overtime_rate=0,
                status="Active"
            )

            db.session.add(employee)
            db.session.flush()

            # Link user with employee
            user.employee_id = employee.id

    db.session.commit()

    flash("Employee approved successfully.", "success")

    return redirect(url_for("admin.pending_users"))


# =====================================
# Reject Employee
# =====================================
@admin.route("/admin/reject/<int:user_id>")
@login_required
def reject_user(user_id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    user = User.query.get_or_404(user_id)

    user.status = "rejected"

    db.session.commit()

    flash("Employee rejected.", "danger")

    return redirect(url_for("admin.pending_users"))


# =====================================
# Approved Employees
# =====================================
@admin.route("/admin/approved_users")
@login_required
def approved_users():

    if not current_user.has_role("Super Admin"):
        abort(403)

    users = User.query.filter_by(
        role="employee",
        status="approved"
    ).all()

    return render_template(
        "admin/approved_users.html",
        users=users
    )


# =====================================
# Rejected Employees
# =====================================
@admin.route("/admin/rejected_users")
@login_required
def rejected_users():

    if not current_user.has_role("Super Admin"):
        abort(403)

    users = User.query.filter_by(
        role="employee",
        status="rejected"
    ).all()

    return render_template(
        "admin/rejected_users.html",
        users=users
    )

# =====================================
# Shift List
# =====================================
@admin.route("/admin/shifts")
@login_required
def shifts():

    if not current_user.has_role("Super Admin"):
        abort(403)

    shifts = Shift.query.all()

    return render_template(
        "admin/shifts.html",
        shifts=shifts
    )


# =====================================
# Add Shift
# =====================================
@admin.route("/admin/add_shift", methods=["GET", "POST"])
@login_required
def add_shift():

    if not current_user.has_role("Super Admin"):
        abort(403)

    if request.method == "POST":

        shift_name = request.form.get("shift_name")

        start_time = datetime.strptime(
            request.form.get("start_time"),
            "%H:%M"
        ).time()

        working_hours = float(
            request.form.get("working_hours")
        )

        # Calculate End Time Automatically
        start_datetime = datetime.combine(
            datetime.today(),
            start_time
        )

        end_datetime = start_datetime + timedelta(
            hours=working_hours
        )

        end_time = end_datetime.time()

        shift = Shift(
            shift_name=shift_name,
            start_time=start_time,
            end_time=end_time,
            working_hours=working_hours
        )

        db.session.add(shift)
        db.session.commit()

        flash("Shift added successfully!", "success")

        return redirect(url_for("admin.shifts"))

    return render_template("admin/add_shift.html")


# =====================================
# Edit Shift
# =====================================
@admin.route("/admin/edit_shift/<int:id>", methods=["GET", "POST"])
@login_required
def edit_shift(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    shift = Shift.query.get_or_404(id)

    if request.method == "POST":

        shift.shift_name = request.form.get("shift_name")

        shift.start_time = datetime.strptime(
            request.form.get("start_time"),
            "%H:%M"
        ).time()

        shift.working_hours = float(
            request.form.get("working_hours")
        )

        # Auto Calculate End Time
        start_datetime = datetime.combine(
            datetime.today(),
            shift.start_time
        )

        end_datetime = start_datetime + timedelta(
            hours=shift.working_hours
        )

        shift.end_time = end_datetime.time()

        db.session.commit()

        flash("Shift updated successfully!", "success")

        return redirect(url_for("admin.shifts"))

    return render_template(
        "admin/edit_shift.html",
        shift=shift
    )


# =====================================
# Delete Shift
# =====================================
@admin.route("/admin/reopen_attendance/<int:id>")
@login_required
def reopen_attendance(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    record = Attendance.query.get_or_404(id)

    record.check_out = None
    record.working_hours = 0
    record.overtime_hours = 0
    record.overtime_pay = 0

    db.session.commit()

    flash("Attendance reopened successfully!", "success")

    return redirect(url_for("admin.dashboard"))

# =====================================
# Delete Shift
# =====================================
@admin.route("/admin/delete_shift/<int:id>")
@login_required
def delete_shift(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    shift = Shift.query.get_or_404(id)

    db.session.delete(shift)
    db.session.commit()

    flash("Shift deleted successfully!", "success")

    return redirect(url_for("admin.shifts"))

# =====================================
# Document Management
# =====================================

ALLOWED_DOCUMENT_EXTENSIONS = {
    "pdf",
    "doc",
    "docx"
}


def allowed_document_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_DOCUMENT_EXTENSIONS
    )


# =====================================
# Document List
# =====================================

@admin.route("/admin/documents")
@login_required
def documents():

    if not current_user.has_role("Super Admin"):
        abort(403)

    documents = Document.query.order_by(
        Document.uploaded_at.desc()
    ).all()

    return render_template(
        "admin/documents.html",
        documents=documents
    )


# =====================================
# Upload Document
# =====================================

@admin.route(
    "/admin/documents/upload",
    methods=["GET", "POST"]
)
@login_required
def upload_document():

    if not current_user.has_role("Super Admin"):
        abort(403)

    employees = Employee.query.order_by(
        Employee.full_name.asc()
    ).all()

    if request.method == "POST":

        title = request.form.get("title", "").strip()

        document_type = request.form.get(
            "document_type",
            ""
        ).strip()

        employee_id = request.form.get(
            "employee_id"
        )

        file = request.files.get("document_file")

        # -----------------------------
        # Basic validation
        # -----------------------------

        if not title:
            flash(
                "Document title is required.",
                "danger"
            )
            return redirect(
                url_for("admin.upload_document")
            )

        if not document_type:
            flash(
                "Document type is required.",
                "danger"
            )
            return redirect(
                url_for("admin.upload_document")
            )

        if not file or not file.filename:
            flash(
                "Please select a document file.",
                "danger"
            )
            return redirect(
                url_for("admin.upload_document")
            )

        if not allowed_document_file(file.filename):
            flash(
                "Only PDF, DOC and DOCX files are allowed.",
                "danger"
            )
            return redirect(
                url_for("admin.upload_document")
            )

        # -----------------------------
        # Employee validation
        # -----------------------------

        employee = None

        if employee_id:

            employee = Employee.query.get(
                int(employee_id)
            )

            if not employee:
                flash(
                    "Selected employee not found.",
                    "danger"
                )
                return redirect(
                    url_for("admin.upload_document")
                )

        # -----------------------------
        # Save file
        # -----------------------------

        upload_folder = os.path.join(
            "uploads",
            "documents"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        original_filename = secure_filename(
            file.filename
        )

        # Prevent duplicate filenames
        filename = (
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}_"
            f"{original_filename}"
        )

        file_path = os.path.join(
            upload_folder,
            filename
        )

        file.save(file_path)

        # -----------------------------
        # Database record
        # -----------------------------

        document = Document(
            employee_id=(
                employee.id
                if employee
                else None
            ),
            title=title,
            document_type=document_type,
            file_name=original_filename,
            file_path=file_path,
            uploaded_by=current_user.id
        )

        db.session.add(document)
        db.session.commit()

        flash(
            "Document uploaded successfully!",
            "success"
        )

        return redirect(
            url_for("admin.documents")
        )

    return render_template(
        "admin/upload_document.html",
        employees=employees
    )

# ==========================
# Activity Logs
# ==========================

@admin.route("/activity-logs")
@login_required
def activity_logs():

    if not current_user.has_role("Super Admin"):
        abort(403)

    logs = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).all()

    return render_template(
        "admin/activity_logs.html",
        logs=logs
    )
# ==========================
# Login History
# ==========================

@admin.route("/login-history")
@login_required
def login_history():

    if not current_user.has_role("Super Admin"):
        abort(403)

    histories = LoginHistory.query.order_by(
        LoginHistory.login_at.desc()
    ).all()

    return render_template(
        "admin/login_history.html",
        histories=histories
    )