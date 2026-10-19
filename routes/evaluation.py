from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models.employee import Employee
from models.evaluation import Evaluation


evaluation = Blueprint(
    "evaluation",
    __name__,
    url_prefix="/evaluation"
)


# ==========================
# Evaluation List
# ==========================

@evaluation.route("/")
@login_required
def evaluation_list():

    if current_user.has_any_role("Super Admin", "HR Manager"):

        evaluations = Evaluation.query.order_by(
            Evaluation.created_at.desc()
        ).all()

    else:

        employee = current_user.employee

        if not employee:
            abort(403)

        evaluations = Evaluation.query.filter_by(
            employee_id=employee.id
        ).order_by(
            Evaluation.created_at.desc()
        ).all()

    return render_template(
        "evaluation/list.html",
        evaluations=evaluations
    )


# ==========================
# Create Evaluation
# ==========================

@evaluation.route("/create", methods=["GET", "POST"])
@login_required
def create_evaluation():

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    employees = Employee.query.filter_by(
        status="Active"
    ).all()

    if request.method == "POST":

        employee_id = request.form.get("employee_id")

        evaluation = Evaluation(
            employee_id=int(employee_id),
            review_period=request.form.get("review_period"),
            rating=float(
                request.form.get("rating") or 0
            ),
            strengths=request.form.get("strengths"),
            weaknesses=request.form.get("weaknesses"),
            comments=request.form.get("comments"),
            manager_feedback=request.form.get(
                "manager_feedback"
            )
        )

        db.session.add(evaluation)
        db.session.commit()

        flash(
            "Performance evaluation created successfully!",
            "success"
        )

        return redirect(
            url_for("evaluation.evaluation_list")
        )

    return render_template(
        "evaluation/create.html",
        employees=employees
    )


# ==========================
# Employee Evaluation View
# ==========================

@evaluation.route("/view/<int:id>")
@login_required
def view_evaluation(id):

    evaluation = Evaluation.query.get_or_404(id)

    if current_user.has_any_role("Super Admin", "HR Manager"):
        pass

    else:

        employee = current_user.employee

        if not employee:
            abort(403)

        if evaluation.employee_id != employee.id:
            abort(403)

    return render_template(
        "evaluation/view.html",
        evaluation=evaluation
    )