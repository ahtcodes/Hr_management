from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models.employee import Employee
from models.leave import Leave
from models.attendance import Attendance
from extensions import db
from datetime import datetime, date

leave = Blueprint("leave", __name__)


# ==========================
# Helper: Check if user is admin
# ==========================
def admin_required():
    """Check if the current user has admin role."""
    if not current_user.is_authenticated or not current_user.has_role("Super Admin"):
        abort(403)  # Forbidden


# ==========================
# Apply Leave
# ==========================
@leave.route("/apply_leave", methods=["GET", "POST"])
@login_required
def apply_leave():

    is_admin = current_user.has_role("Super Admin")
    employees = Employee.query.all() if is_admin else []

    # If employee user, get their linked employee record
    employee_linked = None
    if not is_admin and current_user.employee_id:
        employee_linked = Employee.query.get(current_user.employee_id)

    if request.method == "POST":

        # Determine employee_id: admin picks from dropdown, employee is auto-linked
        if is_admin:
            employee_id = int(request.form.get("employee_id"))
        else:
            if not current_user.employee_id:
                flash("Aap kisi employee se linked nahi hain! Admin se contact karein.", "danger")
                return redirect(url_for("leave.my_leaves"))
            employee_id = current_user.employee_id

        leave_type = request.form.get("leave_type")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        reason = request.form.get("reason")

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        if end_date < start_date:
            flash("End date start date se pehle nahi ho sakti!", "danger")
            return render_template("apply_leave.html", employees=employees, employee_linked=employee_linked, is_admin=is_admin)

        total_days = (end_date - start_date).days + 1

        new_leave = Leave(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            status="Pending"
        )

        db.session.add(new_leave)
        db.session.commit()

        flash("Leave application submit ho gayi hai! Admin approval ka intezaar karein.", "success")
        return redirect(url_for("leave.my_leaves"))

    return render_template(
        "apply_leave.html",
        employees=employees,
        employee_linked=employee_linked,
        is_admin=is_admin
    )


# ==========================
# My Leaves (Employee View)
# ==========================
@leave.route("/my_leaves")
@login_required
def my_leaves():

    is_admin = current_user.has_role("Super Admin")

    if is_admin:
        # Admin sees all leaves
        all_leaves = Leave.query.order_by(Leave.applied_date.desc()).all()
    else:
        # Employee sees only their own leaves
        if current_user.employee_id:
            all_leaves = Leave.query.filter_by(employee_id=current_user.employee_id).order_by(Leave.applied_date.desc()).all()
        else:
            all_leaves = []
            flash("Aap kisi employee se linked nahi hain! Admin se contact karein.", "warning")

    return render_template(
        "my_leaves.html",
        leaves=all_leaves,
        is_admin=is_admin
    )


# ==========================
# Manage Leaves (Admin View)
# ==========================
@leave.route("/manage_leaves")
@login_required
def manage_leaves():

    # Only admin can manage leaves
    if not current_user.has_role("Super Admin"):
        abort(403)
        flash("Sirf admin hi leaves manage kar sakta hai!", "danger")
        return redirect(url_for("leave.my_leaves"))

    # Show all pending leaves first, then approved/rejected
    pending_leaves = Leave.query.filter_by(status="Pending").order_by(Leave.applied_date.desc()).all()
    processed_leaves = Leave.query.filter(Leave.status.in_(["Approved", "Rejected"])).order_by(Leave.applied_date.desc()).all()

    return render_template(
        "manage_leaves.html",
        pending_leaves=pending_leaves,
        processed_leaves=processed_leaves
    )


# ==========================
# Approve Leave
# ==========================

@leave.route("/approve_leave/<int:id>")
@login_required
def approve_leave(id):

    # Only Super Admin can approve leaves
    if not current_user.has_role("Super Admin"):
        flash("Sirf admin hi leave approve kar sakta hai!", "danger")
        return redirect(url_for("leave.manage_leaves"))

    leave_record = Leave.query.get_or_404(id)

    # Approve leave
    leave_record.status = "Approved"
    leave_record.remarks = request.args.get(
        "remarks",
        "Approved by admin"
    )

    db.session.commit()

    # Auto-mark attendance as Leave
    current_date = leave_record.start_date

    while current_date <= leave_record.end_date:

        existing = Attendance.query.filter_by(
            employee_id=leave_record.employee_id,
            date=current_date
        ).first()

        if not existing:

            new_attendance = Attendance(
                employee_id=leave_record.employee_id,
                status="Leave",
                date=current_date,
                check_in=None,
                check_out=None,
                working_hours=0,
                overtime_hours=0,
                overtime_pay=0
            )

            db.session.add(new_attendance)

        else:

            existing.status = "Leave"
            existing.check_in = None
            existing.check_out = None
            existing.working_hours = 0
            existing.overtime_hours = 0
            existing.overtime_pay = 0

        from datetime import timedelta
        current_date += timedelta(days=1)

    db.session.commit()

    flash(
        f"Leave approved! Attendance auto-marked as Leave for "
        f"{leave_record.total_days} day(s).",
        "success"
    )

    return redirect(url_for("leave.manage_leaves"))
# ==========================
# Reject Leave
# ==========================
@leave.route("/reject_leave/<int:id>")
@login_required
def reject_leave(id):

    # Only admin can reject leaves
    if not current_user.has_role("Super Admin"):
           abort(403)
    flash("Sirf admin hi leave reject kar sakta hai!", "danger")
    return redirect(url_for("leave.my_leaves"))

    leave_record = Leave.query.get_or_404(id)

    leave_record.status = "Rejected"
    leave_record.remarks = request.args.get("remarks", "Rejected by admin")
    db.session.commit()

    # Auto-mark attendance as "Absent" for the rejected leave date range
    current_date = leave_record.start_date
    while current_date <= leave_record.end_date:
        # Check if attendance already exists for this date
        existing = Attendance.query.filter_by(
            employee_id=leave_record.employee_id,
            date=current_date
        ).first()

        if not existing:
            new_attendance = Attendance(
                employee_id=leave_record.employee_id,
                status="Absent",
                date=current_date,
                check_in=None,
                check_out=None,
                working_hours=0,
                overtime_hours=0,
                overtime_pay=0
            )
            db.session.add(new_attendance)
        else:
            # If record exists with "Present" or "Leave", change to "Absent"
            existing.status = "Absent"
            existing.check_in = None
            existing.check_out = None
            existing.working_hours = 0
            existing.overtime_hours = 0
            existing.overtime_pay = 0

        # Move to next day
        from datetime import timedelta
        current_date += timedelta(days=1)

    db.session.commit()
    
    flash(f"Leave application reject kar di gayi hai. Attendance 'Absent' mark ki gayi {leave_record.total_days} din ke liye.", "info")
    return redirect(url_for("leave.manage_leaves"))

# ==========================
# Leave History
# ==========================

@leave.route("/leave_history")
@login_required
def leave_history():

    is_admin = current_user.has_role("Super Admin")

    if is_admin:
        # Admin can see all leave history
        leaves = Leave.query.order_by(
            Leave.applied_date.desc()
        ).all()

    else:
        # Employee can see only own leave history
        if not current_user.employee_id:
            flash(
                "Aap kisi employee se linked nahi hain! Admin se contact karein.",
                "warning"
            )
            leaves = []
        else:
            leaves = Leave.query.filter_by(
                employee_id=current_user.employee_id
            ).order_by(
                Leave.applied_date.desc()
            ).all()

    return render_template(
        "leave_history.html",
        leaves=leaves,
        is_admin=is_admin
    )


# ==========================
# Leave Balance
# ==========================

@leave.route("/leave_balance")
@login_required
def leave_balance():

    # Leave limits per year
    leave_limits = {
        "Annual": 14,
        "Casual": 10,
        "Sick": 8
    }

    is_admin = current_user.has_role("Super Admin")

    # ==========================
    # Admin
    # ==========================

    if is_admin:

        employees = Employee.query.order_by(
            Employee.full_name
        ).all()

        balances = []

        current_year = date.today().year

        for employee in employees:

            balance = {}

            for leave_type, allowed_days in leave_limits.items():

                used_days = db.session.query(
                    db.func.coalesce(
                        db.func.sum(Leave.total_days),
                        0
                    )
                ).filter(
                    Leave.employee_id == employee.id,
                    Leave.leave_type == leave_type,
                    Leave.status == "Approved",
                    db.extract("year", Leave.start_date) == current_year
                ).scalar()

                balance[leave_type] = {
                    "allowed": allowed_days,
                    "used": int(used_days or 0),
                    "remaining": max(
                        allowed_days - int(used_days or 0),
                        0
                    )
                }

            balances.append({
                "employee": employee,
                "balance": balance
            })

        return render_template(
            "leave_balance.html",
            balances=balances,
            is_admin=True
        )

    # ==========================
    # Employee
    # ==========================

    if not current_user.employee_id:

        flash(
            "Aap kisi employee se linked nahi hain! Admin se contact karein.",
            "warning"
        )

        return redirect(url_for("leave.my_leaves"))

    employee = Employee.query.get(current_user.employee_id)

    balance = {}

    current_year = date.today().year

    for leave_type, allowed_days in leave_limits.items():

        used_days = db.session.query(
            db.func.coalesce(
                db.func.sum(Leave.total_days),
                0
            )
        ).filter(
            Leave.employee_id == employee.id,
            Leave.leave_type == leave_type,
            Leave.status == "Approved",
            db.extract("year", Leave.start_date) == current_year
        ).scalar()

        balance[leave_type] = {
            "allowed": allowed_days,
            "used": int(used_days or 0),
            "remaining": max(
                allowed_days - int(used_days or 0),
                0
            )
        }

    return render_template(
        "leave_balance.html",
        employee=employee,
        balance=balance,
        is_admin=False
    )