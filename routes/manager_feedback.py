from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models.manager_feedback import ManagerFeedback
from models.employee import Employee


manager_feedback = Blueprint(
    "manager_feedback",
    __name__,
    url_prefix="/manager-feedback"
)


# ==========================
# Feedback List
# ==========================

@manager_feedback.route("/")
@login_required
def feedback_list():

    if current_user.has_any_role("Super Admin", "HR Manager"):

        feedbacks = ManagerFeedback.query.order_by(
            ManagerFeedback.created_at.desc()
        ).all()

    else:

        employee = current_user.employee

        if not employee:
            abort(403)

        feedbacks = ManagerFeedback.query.filter_by(
            employee_id=employee.id
        ).order_by(
            ManagerFeedback.created_at.desc()
        ).all()

    return render_template(
        "manager_feedback/list.html",
        feedbacks=feedbacks
    )


# ==========================
# Create Feedback
# ==========================

@manager_feedback.route("/create", methods=["GET", "POST"])
@login_required
def create_feedback():

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    employees = Employee.query.filter_by(
        status="Active"
    ).all()

    if request.method == "POST":

        new_feedback = ManagerFeedback(

            employee_id=int(
                request.form.get("employee_id")
            ),

            feedback=request.form.get(
                "feedback"
            ),

            rating=float(
                request.form.get("rating") or 0
            )
        )

        db.session.add(new_feedback)
        db.session.commit()

        flash(
            "Manager feedback added successfully!",
            "success"
        )

        return redirect(
            url_for(
                "manager_feedback.feedback_list"
            )
        )

    return render_template(
        "manager_feedback/create.html",
        employees=employees
    )