from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models.kpi import KPI
from models.employee import Employee
from datetime import datetime

kpi = Blueprint(
    "kpi",
    __name__,
    url_prefix="/kpi"
)


# ==================================================
# KPI LIST
# ==================================================

@kpi.route("")
@login_required
def kpi_list():

    # Super Admin / Manager -> all KPIs
    if (
        current_user.has_role("Super Admin")
        or current_user.has_role("Department Manager")
    ):
        kpis = KPI.query.order_by(
            KPI.created_at.desc()
        ).all()

    # Employee -> only own KPIs
    else:

        employee = current_user.employee

        if not employee:
            abort(404)

        kpis = KPI.query.filter_by(
            employee_id=employee.id
        ).order_by(
            KPI.created_at.desc()
        ).all()

    return render_template(
        "kpi/kpis.html",
        kpis=kpis
    )


# ==================================================
# CREATE KPI
# ==================================================

@kpi.route("/create", methods=["GET", "POST"])
@login_required
def create_kpi():

    # Only Super Admin / Department Manager
    if not (
        current_user.has_role("Super Admin")
        or current_user.has_role("Department Manager")
    ):
        abort(403)

    employees = Employee.query.filter_by(
        status="Active"
    ).order_by(
        Employee.full_name
    ).all()

    if request.method == "POST":

        employee_id = request.form.get("employee_id")
        title = request.form.get("title")
        description = request.form.get("description")

        target = float(
            request.form.get("target") or 0
        )

        unit = request.form.get("unit")

        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        start_date_obj = (
            datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()
            if start_date
            else None
        )

        end_date_obj = (
            datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()
            if end_date
            else None
        )

        new_kpi = KPI(

            employee_id=int(employee_id),

            title=title,

            description=description,

            target=target,

            achieved=0,

            unit=unit,

            status="Pending",

            start_date=start_date_obj,

            end_date=end_date_obj
        )

        db.session.add(new_kpi)
        db.session.commit()

        flash(
            "KPI created successfully!",
            "success"
        )

        return redirect(
            url_for("kpi.kpi_list")
        )

    return render_template(
        "kpi/create.html",
        employees=employees
    )


# ==================================================
# UPDATE KPI
# ==================================================

@kpi.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update_kpi(id):

    kpi_data = KPI.query.get_or_404(id)

    # Employee can update achieved value
    if not current_user.has_role("Super Admin"):

        employee = current_user.employee

        if not employee:
            abort(403)

        if kpi_data.employee_id != employee.id:
            abort(403)

    if request.method == "POST":

        achieved = float(
            request.form.get("achieved") or 0
        )

        kpi_data.achieved = achieved

        # Automatically calculate status
        if kpi_data.target > 0:

            if achieved >= kpi_data.target:
                kpi_data.status = "Completed"

            elif achieved > 0:
                kpi_data.status = "In Progress"

            else:
                kpi_data.status = "Pending"

        db.session.commit()

        flash(
            "KPI updated successfully!",
            "success"
        )

        return redirect(
            url_for("kpi.kpi_list")
        )

    return render_template(
        "kpi/update.html",
        kpi=kpi_data
    )


# ==================================================
# DELETE KPI
# ==================================================

@kpi.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_kpi(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    kpi_data = KPI.query.get_or_404(id)

    db.session.delete(kpi_data)
    db.session.commit()

    flash(
        "KPI deleted successfully!",
        "success"
    )

    return redirect(
        url_for("kpi.kpi_list")
    )