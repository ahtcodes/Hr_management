from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models.goal import Goal
from models.employee import Employee


goal = Blueprint(
    "goal",
    __name__,
    url_prefix="/goals"
)


# ==========================
# Goals List
# ==========================

@goal.route("/")
@login_required
def goal_list():

    if current_user.has_any_role("Super Admin", "HR Manager"):

        goals = Goal.query.order_by(
            Goal.created_at.desc()
        ).all()

    else:

        employee = current_user.employee

        if not employee:
            abort(403)

        goals = Goal.query.filter_by(
            employee_id=employee.id
        ).order_by(
            Goal.created_at.desc()
        ).all()

    return render_template(
        "goal/list.html",
        goals=goals
    )


# ==========================
# Create Goal
# ==========================

@goal.route("/create", methods=["GET", "POST"])
@login_required
def create_goal():

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    employees = Employee.query.filter_by(
        status="Active"
    ).all()

    if request.method == "POST":

        new_goal = Goal(
            employee_id=int(
                request.form.get("employee_id")
            ),

            title=request.form.get("title"),

            description=request.form.get(
                "description"
            ),

            target=request.form.get(
                "target"
            ),

            progress=float(
                request.form.get("progress") or 0
            ),

            status=request.form.get(
                "status"
            ) or "Pending",

            start_date=request.form.get(
                "start_date"
            ) or None,

            end_date=request.form.get(
                "end_date"
            ) or None
        )

        db.session.add(new_goal)
        db.session.commit()

        flash(
            "Goal created successfully!",
            "success"
        )

        return redirect(
            url_for("goal.goal_list")
        )

    return render_template(
        "goal/create.html",
        employees=employees
    )