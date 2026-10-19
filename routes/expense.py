from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models.expense import Expense
from models.employee import Employee
from extensions import db
from datetime import datetime


expense = Blueprint(
    "expense",
    __name__,
    url_prefix="/expenses"
)

# ==========================
#  Expense list
# ==========================
@expense.route("/")
@login_required
def expense_list():

    # Super Admin → all expenses
    if (
        current_user.role
        and current_user.role.name == "Super Admin"
    ):

        expenses = Expense.query.order_by(
            Expense.created_at.desc()
        ).all()

    else:

        # Employee must be linked with Employee record
        if not current_user.employee_id:
            abort(403)

        employee = Employee.query.get(
            current_user.employee_id
        )

        if not employee:
            abort(403)

        # Employee → only own expenses
        expenses = Expense.query.filter_by(
            employee_id=employee.id
        ).order_by(
            Expense.created_at.desc()
        ).all()

    return render_template(
        "expense/list.html",
        expenses=expenses
    )
# ==========================
# Create Expense Request
# ==========================

@expense.route("/create", methods=["GET", "POST"])
@login_required
def create_expense():

    # Employee ID comes directly from User
    if not current_user.employee_id:
        abort(403)

    employee = Employee.query.get(
        current_user.employee_id
    )

    if not employee:
        abort(403)

    if request.method == "POST":

        title = request.form.get("title")
        category = request.form.get("category")
        amount = request.form.get("amount")
        expense_date = request.form.get("expense_date")
        description = request.form.get("description")

        # Required fields
        if not title or not category or not amount or not expense_date:

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(
                url_for("expense.create_expense")
            )

        # Convert amount and date
        try:

            amount = float(amount)

            if amount <= 0:
                raise ValueError

            parsed_date = datetime.strptime(
                expense_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid amount or date.",
                "danger"
            )

            return redirect(
                url_for("expense.create_expense")
            )

        # Create expense
        new_expense = Expense(
            employee_id=employee.id,
            title=title,
            category=category,
            amount=amount,
            expense_date=parsed_date,
            description=description,
            status="Pending",
            reimbursement_status="Pending"
        )

        db.session.add(new_expense)
        db.session.commit()

        flash(
            "Expense request submitted successfully!",
            "success"
        )

        return redirect(
            url_for("expense.expense_list")
        )

    return render_template(
        "expense/create.html"
    )


# ==========================
# Approve Expense
# ==========================

@expense.route(
    "/approve/<int:id>",
    methods=["POST"]
)
@login_required
def approve_expense(id):

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    expense_data = Expense.query.get_or_404(id)

    expense_data.status = "Approved"
    expense_data.approved_by = current_user.id
    expense_data.approved_at = datetime.utcnow()

    db.session.commit()

    flash(
        "Expense approved successfully!",
        "success"
    )

    return redirect(
        url_for("expense.expense_list")
    )


# ==========================
# Reject Expense
# ==========================

@expense.route(
    "/reject/<int:id>",
    methods=["POST"]
)
@login_required
def reject_expense(id):

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    expense_data = Expense.query.get_or_404(id)

    expense_data.status = "Rejected"

    db.session.commit()

    flash(
        "Expense rejected successfully!",
        "success"
    )

    return redirect(
        url_for("expense.expense_list")
    )


# ==========================
# Mark Reimbursement
# ==========================

@expense.route(
    "/reimburse/<int:id>",
    methods=["POST"]
)
@login_required
def reimburse_expense(id):

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    expense_data = Expense.query.get_or_404(id)

    # Only approved expenses can be reimbursed
    if expense_data.status != "Approved":

        flash(
            "Only approved expenses can be reimbursed.",
            "danger"
        )

        return redirect(
            url_for("expense.expense_list")
        )

    expense_data.reimbursement_status = "Reimbursed"
    expense_data.reimbursed_at = datetime.utcnow()

    db.session.commit()

    flash(
        "Expense reimbursed successfully!",
        "success"
    )

    return redirect(
        url_for("expense.expense_list")
    )

