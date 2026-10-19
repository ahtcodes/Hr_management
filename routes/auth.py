from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from models.login_history import LoginHistory
from models.user import User
from extensions import db, bcrypt
from datetime import datetime, date
from models.role import Role
from models.attendance import Attendance
from models.employee import Employee

# Activity Log
from utils.activity import log_activity


auth = Blueprint("auth", __name__)


# ==========================
# Login
# ==========================

# ==========================
# Login
# ==========================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter(
            (User.username == username) |
            (User.email == username)
        ).first()

        # ==========================
        # Invalid Login
        # ==========================

        if not user or not bcrypt.check_password_hash(
            user.password,
            password
        ):

            flash(
                "Invalid Username/Email or Password",
                "danger"
            )

            return render_template("login.html")

        # ==========================
        # Employee Approval Check
        # ==========================

        if user.has_role("Employee"):

            if user.status == "pending":

                flash(
                    "Your account is waiting for admin approval.",
                    "warning"
                )

                return redirect(
                    url_for("auth.login")
                )

            elif user.status == "rejected":

                flash(
                    "Your account has been rejected by admin.",
                    "danger"
                )

                return redirect(
                    url_for("auth.login")
                )

        # ==========================
        # Login User
        # ==========================

        login_user(user)

        # ==========================
        # Auto Check In Employee
        # ==========================

        if user.has_role("Employee") and user.employee:

            today = date.today()

            attendance = Attendance.query.filter_by(
                employee_id=user.employee.id,
                date=today
            ).first()

            if attendance is None:

                attendance = Attendance(
                    employee_id=user.employee.id,
                    date=today,
                    status="Present",
                    check_in=datetime.now().time(),
                    shift_start=(
                        user.employee.shift.start_time
                        if user.employee.shift
                        else None
                    ),
                    shift_end=(
                        user.employee.shift.end_time
                        if user.employee.shift
                        else None
                    ),
                    working_hours=0,
                    overtime_hours=0,
                    overtime_pay=0
                )

                db.session.add(attendance)

            elif attendance.check_in is None:

                attendance.check_in = datetime.now().time()
                attendance.status = "Present"

            db.session.commit()

        # =========================
        # Role Based Redirect
        # =========================

        if user.has_any_role("Super Admin","HR Manager"):

            return redirect(
                url_for("admin.dashboard")
            )

        elif user.has_role("HR Manager"):

            return redirect(
                url_for("admin.dashboard")
            )

        elif user.has_role("Department Manager"):

            return redirect(
                url_for("employee.employee_dashboard")
            )

        elif user.has_role("Employee"):

            return redirect(
                url_for("employee.employee_dashboard")
            )

        else:

            flash(
                "Your account does not have a valid role.",
                "danger"
            )

            logout_user()

            return redirect(
                url_for("auth.login")
            )

    # ==========================
    # GET REQUEST
    # ==========================

    return render_template("login.html")
# ==========================
# Register
# ==========================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # ==========================
        # Check Username
        # ==========================

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            flash(
                "Username already exists!",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ==========================
        # Check Email
        # ==========================

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash(
                "Email already registered!",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ==========================
        # Password Hash
        # ==========================

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        # ==========================
        # Role
        # ==========================

        role_name = request.form.get(
            "role",
            "Employee"
        )

        role = Role.query.filter_by(
            name=role_name
        ).first()

        if role is None:

            flash(
                "Selected role does not exist.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ==========================
        # Create User
        # ==========================

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role,
            status=(
                "approved"
                if role.name == "Super Admin"
                else "pending"
            )
        )

        try:

            db.session.add(user)
            db.session.commit()

            # ==========================
            # Registration Message
            # ==========================

            if role.name == "Employee":

                flash(
                    "Registration successful! "
                    "Please wait for admin approval.",
                    "info"
                )

            else:

                flash(
                    "Admin registration successful!",
                    "success"
                )

            return redirect(
                url_for("auth.login")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                f"Registration failed: {str(e)}",
                "danger"
            )

    return render_template(
        "register.html"
    )


# ==========================
# Forgot Password
# ==========================

@auth.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        username_or_email = request.form.get(
            "username_or_email"
        )

        user = User.query.filter(
            (User.username == username_or_email) |
            (User.email == username_or_email)
        ).first()

        if not user:

            flash(
                "No account found with this username or email.",
                "danger"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        return redirect(
            url_for(
                "auth.reset_password",
                user_id=user.id
            )
        )

    return render_template(
        "forgot_password.html"
    )


# ==========================
# Reset Password
# ==========================

@auth.route(
    "/reset-password/<int:user_id>",
    methods=["GET", "POST"]
)
def reset_password(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == "POST":

        new_password = request.form.get(
            "new_password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )

        # ==========================
        # Empty Password
        # ==========================

        if not new_password:

            flash(
                "Please enter a new password.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    user_id=user.id
                )
            )

        # ==========================
        # Password Length
        # ==========================

        if len(new_password) < 8:

            flash(
                "Password must be at least 8 characters.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    user_id=user.id
                )
            )

        # ==========================
        # Confirm Password
        # ==========================

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    user_id=user.id
                )
            )

        # ==========================
        # Update Password
        # ==========================

        user.password = bcrypt.generate_password_hash(
            new_password
        ).decode("utf-8")

        db.session.commit()

        flash(
            "Password reset successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "reset_password.html",
        user=user
    )


# ==========================
# Logout
# ==========================

@auth.route("/logout")
@login_required
def logout():

    if current_user.has_role("Employee") and current_user.employee:

        today = date.today()

        attendance = Attendance.query.filter_by(
            employee_id=current_user.employee.id,
            date=today
        ).first()

        if attendance and attendance.check_out is None:

            attendance.check_out = datetime.now().time()

            in_minutes = (
                attendance.check_in.hour * 60 +
                attendance.check_in.minute
            )

            out_minutes = (
                attendance.check_out.hour * 60 +
                attendance.check_out.minute
            )

            diff = out_minutes - in_minutes

            if diff < 0:
                diff += 24 * 60

            attendance.working_hours = round(
                diff / 60,
                2
            )

            if current_user.employee.shift:

                shift_hours = (
                    current_user.employee.shift.working_hours
                )

                if attendance.working_hours > shift_hours:

                    attendance.overtime_hours = round(
                        attendance.working_hours - shift_hours,
                        2
                    )

                    attendance.overtime_pay = round(
                        attendance.overtime_hours *
                        current_user.employee.overtime_rate,
                        2
                    )

            db.session.commit()

    logout_user()

    return redirect(
        url_for("auth.login")
    )