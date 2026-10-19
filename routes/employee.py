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
from models.role import Role
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
from sqlalchemy import text
import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from models.document import Document
from extensions import db
from models.employee import Employee, Department, Designation


employee = Blueprint("employee", __name__)


# ==========================
# Employee Dashboard
# ==========================
@employee.route("/employee/dashboard")
@login_required
def employee_dashboard():

    if not current_user.has_any_role("employee","HR Manager"):
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

    # Super Admin / HR Manager / Department Manager
    if not current_user.has_any_role(
        "Super Admin",
        "HR Manager",
        "Department Manager"
    ):
        abort(403)

    # ==========================
    # Super Admin + HR Manager
    # ==========================

    if current_user.has_any_role(
        "Super Admin",
        "HR Manager"
    ):
        all_employees = Employee.query.all()

    # ==========================
    # Department Manager
    # ==========================

    else:

        manager_employee = current_user.employee

        if not manager_employee:
            abort(403)

        department_id = manager_employee.department_id

        if not department_id:
            abort(403)

        all_employees = Employee.query.filter_by(
            department_id=department_id
        ).all()

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

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    employee = Employee.query.get_or_404(id)

    # ==========================
    # Dropdown Data
    # ==========================

    shifts = Shift.query.all()

    departments = Department.query.order_by(
        Department.name
    ).all()

    designations = Designation.query.order_by(
        Designation.name
    ).all()

    # ==========================
    # POST
    # ==========================

    if request.method == "POST":

        # ==========================
        # Basic Information
        # ==========================

        employee.full_name = request.form.get("full_name")
        employee.email = request.form.get("email")
        employee.phone = request.form.get("phone")

        # ==========================
        # Department
        # ==========================

        department_id = request.form.get("department_id")

        employee.department_id = (
            int(department_id)
            if department_id
            else None
        )

        # ==========================
        # Designation
        # ==========================

        designation_id = request.form.get("designation_id")

        employee.designation_id = (
            int(designation_id)
            if designation_id
            else None
        )

        # ==========================
        # Shift
        # ==========================

        shift_id = request.form.get("shift_id")

        employee.shift_id = (
            int(shift_id)
            if shift_id
            else None
        )

        # ==========================
        # Joining Date
        # ==========================

        joining_date_str = request.form.get("joining_date")

        if joining_date_str:
            employee.joining_date = datetime.strptime(
                joining_date_str,
                "%Y-%m-%d"
            ).date()
        else:
            employee.joining_date = None

        # ==========================
        # Resignation Date
        # ==========================

        resignation_date_str = request.form.get(
            "resignation_date"
        )

        if resignation_date_str:
            employee.resignation_date = datetime.strptime(
                resignation_date_str,
                "%Y-%m-%d"
            ).date()
        else:
            employee.resignation_date = None

        # ==========================
        # Employment Information
        # ==========================

        employee.employment_type = request.form.get(
            "employment_type"
        )

        employee.location = request.form.get(
            "location"
        )

        # ==========================
        # Salary
        # ==========================

        basic_salary = request.form.get("basic_salary")
        overtime_rate = request.form.get("overtime_rate")

        employee.basic_salary = (
            float(basic_salary)
            if basic_salary
            else 0
        )

        employee.overtime_rate = (
            float(overtime_rate)
            if overtime_rate
            else 0
        )

        # ==========================
        # Status
        # ==========================

        employee.status = request.form.get(
            "status",
            "Active"
        )

        # ==========================
        # Emergency Contact
        # ==========================

        employee.emergency_contact_name = request.form.get(
            "emergency_contact_name"
        )

        employee.emergency_contact_relation = request.form.get(
            "emergency_contact_relation"
        )

        employee.emergency_contact_phone = request.form.get(
            "emergency_contact_phone"
        )

        # ==========================
        # Save
        # ==========================

        try:

            db.session.commit()

            flash(
                "Employee updated successfully!",
                "success"
            )

            return redirect(
                url_for("employee.employees")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                f"Error updating employee: {str(e)}",
                "danger"
            )

    # ==========================
    # Render
    # ==========================

    return render_template(
        "edit_employee.html",
        employee=employee,
        shifts=shifts,
        departments=departments,
        designations=designations
    )
# ==========================
# Delete Employee
# ==========================
@employee.route("/delete_employee/<int:id>", methods=["POST"])
@login_required
def delete_employee(id):

    if not current_user.has_any_role(
        "Super Admin",
        "Admin",
        "HR Manager"
    ):
        abort(403)

    employee = Employee.query.get_or_404(id)

    try:

        # =====================================================
        # 1. Find User linked with this Employee
        # =====================================================

        users = User.query.filter_by(
            employee_id=id
        ).all()

        user_ids = [
            user.id
            for user in users
        ]


        # =====================================================
        # 2. Delete Messages + Conversations
        # =====================================================

        conversation_ids = []

        for user_id in user_ids:

            rows = db.session.execute(
                text("""
                    SELECT id
                    FROM conversations
                    WHERE user1_id = :user_id
                       OR user2_id = :user_id
                """),
                {
                    "user_id": user_id
                }
            ).scalars().all()

            conversation_ids.extend(rows)


        # Remove duplicate conversation IDs
        conversation_ids = list(set(conversation_ids))


        # -----------------------------------------------------
        # Delete messages belonging to conversations
        # -----------------------------------------------------

        for conversation_id in conversation_ids:

            db.session.execute(
                text("""
                    DELETE FROM messages
                    WHERE conversation_id = :conversation_id
                """),
                {
                    "conversation_id": conversation_id
                }
            )


        # -----------------------------------------------------
        # Delete messages where employee user is sender/receiver
        # -----------------------------------------------------

        for user_id in user_ids:

            db.session.execute(
                text("""
                    DELETE FROM messages
                    WHERE sender_id = :user_id
                       OR receiver_id = :user_id
                """),
                {
                    "user_id": user_id
                }
            )


        db.session.flush()


        # -----------------------------------------------------
        # Delete conversations
        # -----------------------------------------------------

        for conversation_id in conversation_ids:

            db.session.execute(
                text("""
                    DELETE FROM conversations
                    WHERE id = :conversation_id
                """),
                {
                    "conversation_id": conversation_id
                }
            )


        db.session.flush()


        # =====================================================
        # 3. Delete Asset Assignments
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM asset_assignments
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 4. Delete Attendance
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM attendance
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 5. Delete Documents
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM documents
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 6. Delete Evaluations
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM evaluations
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 7. Delete Expenses
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM expenses
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 8. Delete Goals
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM goals
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 9. Delete KPIs
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM kpis
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 10. Delete Leaves
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM leaves
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 11. Delete Manager Feedback
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM manager_feedback
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        # =====================================================
        # 12. Delete Payrolls
        # =====================================================

        db.session.execute(
            text("""
                DELETE FROM payrolls
                WHERE employee_id = :employee_id
            """),
            {
                "employee_id": id
            }
        )


        db.session.flush()


        # =====================================================
        # 13. Delete User Account
        # =====================================================

        for user in users:

            db.session.delete(user)

        db.session.flush()


        # =====================================================
        # 14. Delete Employee
        # =====================================================

        db.session.delete(employee)

        db.session.flush()


        # =====================================================
        # 15. Commit
        # =====================================================

        db.session.commit()


        flash(
            "Employee and all related records deleted successfully!",
            "success"
        )


    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(
            "Employee deletion failed. Employee ID: %s",
            id
        )

        flash(
            f"Employee delete nahi hua: {str(e)}",
            "danger"
        )


    return redirect(
        url_for("employee.employees")
    )

# ==========================
# Add Employee (Admin Only)
# ==========================
@employee.route("/add_employee", methods=["GET", "POST"])
@login_required
def add_employee():

    if not current_user.has_any_role(
        "Super Admin",
        "HR Manager"
    ):
        abort(403)

    # ==========================
    # Dropdown Data
    # ==========================

    shifts = Shift.query.all()

    departments = Department.query.order_by(
        Department.name
    ).all()

    designations = Designation.query.order_by(
        Designation.name
    ).all()

    # ==========================
    # Generate Next Employee Code
    # ==========================

    last_employee = Employee.query.order_by(
        Employee.id.desc()
    ).first()

    if last_employee and last_employee.employee_code:

        try:

            last_number = int(
                last_employee.employee_code.replace(
                    "EMP",
                    ""
                )
            )

            next_employee_code = (
                f"EMP{last_number + 1:04d}"
            )

        except ValueError:

            next_employee_code = "EMP0001"

    else:

        next_employee_code = "EMP0001"


    # ==========================
    # POST
    # ==========================

    if request.method == "POST":

        profile_photo = request.files.get(
            "profile_photo"
        )

        cnic_file = request.files.get(
            "cnic_file"
        )

        cv_file = request.files.get(
            "cv_file"
        )

        certificate_file = request.files.get(
            "certificate_file"
        )

        profile_photo_name = None
        cnic_name = None
        cv_name = None
        certificate_name = None


        # ==========================
        # Resignation Date
        # ==========================

        resignation_date_str = request.form.get(
            "resignation_date"
        )

        if resignation_date_str:

            resignation_date = datetime.strptime(
                resignation_date_str,
                "%Y-%m-%d"
            ).date()

        else:

            resignation_date = None


        try:

            # ==========================
            # Get Foreign Key IDs
            # ==========================

            department_id = request.form.get(
                "department_id"
            )

            designation_id = request.form.get(
                "designation_id"
            )

            shift_id = request.form.get(
                "shift_id"
            )


            # ==========================
            # Validate Department
            # ==========================

            department = None

            if department_id:

                department = Department.query.get(
                    int(department_id)
                )

                if not department:

                    flash(
                        "Selected department does not exist.",
                        "danger"
                    )

                    return render_template(
                        "add_employee.html",
                        shifts=shifts,
                        departments=departments,
                        designations=designations,
                        next_employee_code=next_employee_code
                    )


            # ==========================
            # Validate Designation
            # ==========================

            designation = None

            if designation_id:

                designation = Designation.query.get(
                    int(designation_id)
                )

                if not designation:

                    flash(
                        "Selected designation does not exist.",
                        "danger"
                    )

                    return render_template(
                        "add_employee.html",
                        shifts=shifts,
                        departments=departments,
                        designations=designations,
                        next_employee_code=next_employee_code
                    )


            # ==========================
            # Validate Shift
            # ==========================

            shift = None

            if shift_id:

                shift = Shift.query.get(
                    int(shift_id)
                )

                if not shift:

                    flash(
                        "Selected shift does not exist.",
                        "danger"
                    )

                    return render_template(
                        "add_employee.html",
                        shifts=shifts,
                        departments=departments,
                        designations=designations,
                        next_employee_code=next_employee_code
                    )


            # ==========================
            # Create Employee
            # ==========================

            new_employee = Employee(

                profile_photo=profile_photo_name,
                cnic_file=cnic_name,
                cv_file=cv_name,
                certificate_file=certificate_name,

                employee_code=next_employee_code,

                full_name=request.form.get(
                    "full_name"
                ),

                email=request.form.get(
                    "email"
                ),

                phone=request.form.get(
                    "phone"
                ),

                # IMPORTANT:
                # Foreign Key IDs use honge
                department_id=(
                    int(department_id)
                    if department_id
                    else None
                ),

                designation_id=(
                    int(designation_id)
                    if designation_id
                    else None
                ),

                joining_date=datetime.strptime(
                    request.form.get(
                        "joining_date"
                    ),
                    "%Y-%m-%d"
                ).date(),

                resignation_date=resignation_date,

                basic_salary=float(
                    request.form.get(
                        "basic_salary"
                    ) or 0
                ),

                overtime_rate=float(
                    request.form.get(
                        "overtime_rate"
                    ) or 0
                ),

                shift_id=(
                    int(shift_id)
                    if shift_id
                    else None
                ),

                employment_type=request.form.get(
                    "employment_type"
                ),

                location=request.form.get(
                    "location"
                ),

                status=request.form.get(
                    "status",
                    "Active"
                ),

                emergency_contact_name=request.form.get(
                    "emergency_contact_name"
                ),

                emergency_contact_relation=request.form.get(
                    "emergency_contact_relation"
                ),

                emergency_contact_phone=request.form.get(
                    "emergency_contact_phone"
                )
            )


            # ==========================
            # Save Employee
            # ==========================

            db.session.add(new_employee)

            # Employee ID generate karne ke liye flush
            db.session.flush()


            # ==========================
            # Find Employee Role
            # ==========================

            employee_role = Role.query.filter_by(
                name="Employee"
            ).first()

            if employee_role is None:

                db.session.rollback()

                flash(
                    "Employee role does not exist in database.",
                    "danger"
                )

                return render_template(
                    "add_employee.html",
                    shifts=shifts,
                    departments=departments,
                    designations=designations,
                    next_employee_code=next_employee_code
                )


            # ==========================
            # Create Attendance
            # ==========================

            attendance = Attendance(

                employee_id=new_employee.id,

                status="Absent",

                check_in=None,

                check_out=None,

                shift_id=new_employee.shift_id,

                shift_start=(
                    new_employee.shift.start_time
                    if new_employee.shift
                    else None
                ),

                shift_end=(
                    new_employee.shift.end_time
                    if new_employee.shift
                    else None
                ),

                working_hours=0,

                overtime_hours=0,

                overtime_pay=0,

                date=date.today()
            )

            db.session.add(attendance)


            # ==========================
            # Default Password
            # ==========================

            hashed_password = (
                bcrypt
                .generate_password_hash(
                    "employee123"
                )
                .decode("utf-8")
            )


            # ==========================
            # Create User
            # ==========================

            user = User(

                username=new_employee.email,

                email=new_employee.email,

                password=hashed_password,

                # Role object
                role=employee_role,

                employee_id=new_employee.id,

                status="approved"
            )

            db.session.add(user)


            # ==========================
            # Commit
            # ==========================

            db.session.commit()


            flash(
                f"Employee added successfully! "
                f"Employee Code: "
                f"{new_employee.employee_code} "
                f"| Default Password: employee123",
                "success"
            )


            return redirect(
                url_for(
                    "employee.employees"
                )
            )


        except IntegrityError as e:

            db.session.rollback()

            print(
                "DATABASE ERROR:",
                e.orig
            )

            flash(
                f"Database error: {e.orig}",
                "danger"
            )


        except Exception as e:

            db.session.rollback()

            current_app.logger.exception(
                "Employee creation failed"
            )

            flash(
                f"Employee creation failed: {str(e)}",
                "danger"
            )


    # ==========================
    # GET
    # ==========================

    return render_template(
        "add_employee.html",
        shifts=shifts,
        departments=departments,
        designations=designations,
        next_employee_code=next_employee_code
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

    # =========================================
# Employee Profile - Update Profile Photo
# =========================================

@employee.route("/employee/profile", methods=["GET", "POST"])
@login_required
def employee_profile():

    employee_data = current_user.employee

    if not employee_data:
        abort(404)

    if request.method == "POST":

        profile_photo = request.files.get("profile_photo")

        if not profile_photo or not profile_photo.filename:
            flash(
                "Please select a profile picture.",
                "warning"
            )

            return redirect(
                url_for("employee.employee_profile")
            )

        # =========================================
        # Allowed Extensions
        # =========================================

        allowed_extensions = {
            "jpg",
            "jpeg",
            "png",
            "webp"
        }

        filename = secure_filename(
            profile_photo.filename
        )

        extension = (
            filename.rsplit(".", 1)[1].lower()
            if "." in filename
            else ""
        )

        if extension not in allowed_extensions:

            flash(
                "Only JPG, JPEG, PNG and WEBP images are allowed.",
                "danger"
            )

            return redirect(
                url_for("employee.employee_profile")
            )

        # =========================================
        # Upload Directory
        # =========================================

        upload_folder = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "profile_photos"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        # =========================================
        # Unique Filename
        # =========================================

        new_filename = (
            f"employee_{employee_data.id}_"
            f"{uuid4().hex}.{extension}"
        )

        file_path = os.path.join(
            upload_folder,
            new_filename
        )

        # =========================================
        # Delete Previous Photo
        # =========================================

        if employee_data.profile_photo:

            old_photo = os.path.join(
                current_app.root_path,
                "static",
                employee_data.profile_photo
            )

            if os.path.exists(old_photo):

                try:
                    os.remove(old_photo)
                except OSError:
                    pass

        # =========================================
        # Save New Photo
        # =========================================

        profile_photo.save(file_path)

        # Database mein relative path save hoga
        employee_data.profile_photo = (
            f"uploads/profile_photos/{new_filename}"
        )

        db.session.commit()

        flash(
            "Profile picture updated successfully.",
            "success"
        )

        return redirect(
            url_for("employee.employee_profile")
        )

    return render_template(
        "employee/profile.html",
        employee=employee_data
    )
@employee.route("/department/dashboard")
@login_required
def department_dashboard():

    print("========== DEPARTMENT DASHBOARD ==========")
    print("User ID:", current_user.id)
    print("Username:", current_user.username)
    print(
        "Role:",
        current_user.role.name if current_user.role else None
    )
    print("Role ID:", current_user.role_id)
    print("Employee ID:", current_user.employee_id)

    # Department Manager check
    if not current_user.has_role("Department Manager"):
        print("❌ ROLE CHECK FAILED")
        abort(403)

    manager_employee = current_user.employee

    print("Manager Employee:", manager_employee)

    if not manager_employee:
        print("❌ EMPLOYEE NOT FOUND")
        abort(403)

    department_id = manager_employee.department_id

    print("Department ID:", department_id)
    print(
        "Department:",
        manager_employee.department.name
        if manager_employee.department
        else None
    )

    if not department_id:
        print("❌ DEPARTMENT ID NOT FOUND")
        abort(403)

    # Department employees
    department_employees = Employee.query.filter_by(
        department_id=department_id
    ).all()

    print(
        "Department Employees:",
        [
            (e.id, e.full_name)
            for e in department_employees
        ]
    )

    employee_ids = [
        emp.id for emp in department_employees
    ]

    total_employees = len(department_employees)

    # Today's attendance
    today_attendance = Attendance.query.filter(
        Attendance.employee_id.in_(employee_ids),
        Attendance.date == date.today()
    ).all()

    present_today = sum(
        1
        for attendance in today_attendance
        if attendance.status == "Present"
    )

    # Today's approved leaves
    today = date.today()

    today_leaves = Leave.query.filter(
        Leave.employee_id.in_(employee_ids),
        Leave.status.in_(["Approved", "approved"]),
        Leave.start_date <= today,
        Leave.end_date >= today
    ).all()

    on_leave_today = len(today_leaves)

    absent_today = max(
        total_employees - present_today - on_leave_today,
        0
    )

    print("Total Employees:", total_employees)
    print("Present Today:", present_today)
    print("On Leave Today:", on_leave_today)
    print("Absent Today:", absent_today)
    print("========== DASHBOARD SUCCESS ==========")

    return render_template(
        "department/dashboard.html",
        department=manager_employee.department,
        department_employees=department_employees,
        total_employees=total_employees,
        present_today=present_today,
        absent_today=absent_today,
        on_leave_today=on_leave_today
    )
@employee.route("/department/employees")
@login_required
def department_employees():

    if not current_user.has_role("Department Manager"):
        abort(403)

    manager_employee = current_user.employee

    if not manager_employee:
        abort(403)

    department_id = manager_employee.department_id

    if not department_id:
        abort(403)

    employees = Employee.query.filter_by(
        department_id=department_id
    ).all()

    return render_template(
        "department/employees.html",
        employees=employees,
        department=manager_employee.department
    )

@employee.route("/department/attendance")
@login_required
def department_attendance():

    if not current_user.has_role("Department Manager"):
        abort(403)

    manager_employee = current_user.employee

    if not manager_employee:
        abort(403)

    department_id = manager_employee.department_id

    if not department_id:
        abort(403)

    # Sirf manager ke department ke employees
    employees = Employee.query.filter_by(
        department_id=department_id
    ).all()

    employee_ids = [employee.id for employee in employees]

    # Sirf un employees ki attendance
    attendance = Attendance.query.filter(
        Attendance.employee_id.in_(employee_ids)
    ).order_by(
        Attendance.date.desc()
    ).all()

    return render_template(
        "department/attendance.html",
        attendance=attendance,
        employees=employees,
        department=manager_employee.department
    )


@employee.route("/department/leaves")
@login_required
def department_leaves():

    if not current_user.has_role("Department Manager"):
        abort(403)

    manager_employee = current_user.employee

    if not manager_employee:
        abort(403)

    department_id = manager_employee.department_id

    if not department_id:
        abort(403)

    employees = Employee.query.filter_by(
        department_id=department_id
    ).all()

    employee_ids = [e.id for e in employees]

    leaves = Leave.query.filter(
        Leave.employee_id.in_(employee_ids)
    ).all()

    return render_template(
        "department/leaves.html",
        leaves=leaves,
        employees=employees,
        department=manager_employee.department
    )

@employee.route("/department/leave/<int:id>/approve", methods=["POST"])
@login_required
def approve_department_leave(id):

    if not current_user.has_role("Department Manager"):
        abort(403)

    manager_employee = current_user.employee

    if not manager_employee:
        abort(403)

    leave = Leave.query.get_or_404(id)

    # Leave employee exist karta hai?
    if not leave.employee:
        abort(404)

    # IMPORTANT:
    # Leave sirf manager ke department ki honi chahiye
    if leave.employee.department_id != manager_employee.department_id:
        abort(403)

    leave.status = "Approved"

    db.session.commit()

    flash(
        "Leave approved successfully.",
        "success"
    )

    return redirect(
        url_for("employee.department_leaves")
    )

@employee.route("/department/leave/<int:leave_id>/reject", methods=["POST"])
@login_required
def reject_department_leave(leave_id):

    if not current_user.has_role("Department Manager"):
        abort(403)

    leave = Leave.query.get_or_404(leave_id)

    manager_department_id = current_user.employee.department_id

    leave_employee = Employee.query.get(leave.employee_id)

    # Sirf same department
    if not leave_employee or leave_employee.department_id != manager_department_id:
        abort(403)

    leave.status = "Rejected"

    db.session.commit()

    flash("Leave rejected successfully.", "success")

    return redirect(
        url_for("employee.department_leaves")
    )