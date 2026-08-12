from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime

from extensions import db
from models.holiday import Holiday


holiday = Blueprint(
    "holiday",
    __name__,
    url_prefix="/holiday"
)

@holiday.route("/", methods=["GET"])
@login_required
def holiday_list():

    # Super Admin + Employee dono holidays dekh sakte hain
    holidays = Holiday.query.order_by(
        Holiday.date.asc()
    ).all()

    return render_template(
        "holiday/list.html",
        holidays=holidays
    )
# ==========================
# Add Holiday
# ==========================

@holiday.route("/add", methods=["GET", "POST"])
@login_required
def add_holiday():

    if not current_user.has_role("Super Admin"):
        abort(403)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        holiday_date = request.form.get("date")
        holiday_type = request.form.get(
            "holiday_type",
            "Public"
        )

        description = request.form.get(
            "description",
            ""
        ).strip()

        # ==========================
        # Validation
        # ==========================

        if not name or not holiday_date:

            flash(
                "Holiday name and date are required.",
                "danger"
            )

            return redirect(
                url_for("holiday.add_holiday")
            )

        try:

            holiday_date = datetime.strptime(
                holiday_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid holiday date.",
                "danger"
            )

            return redirect(
                url_for("holiday.add_holiday")
            )

        # ==========================
        # Check Duplicate
        # ==========================

        existing = Holiday.query.filter_by(
            date=holiday_date
        ).first()

        if existing:

            flash(
                f"A holiday already exists on "
                f"{holiday_date.strftime('%d %b %Y')}.",
                "warning"
            )

            return redirect(
                url_for("holiday.add_holiday")
            )

        # ==========================
        # Create Holiday
        # ==========================

        new_holiday = Holiday(
            name=name,
            date=holiday_date,
            holiday_type=holiday_type,
            description=description,
            status="Active"
        )

        db.session.add(new_holiday)
        db.session.commit()

        flash(
            "Holiday added successfully!",
            "success"
        )

        return redirect(
            url_for("holiday.holiday_list")
        )

    return render_template(
        "holiday/add.html"
    )


# ==========================
# Edit Holiday
# ==========================

@holiday.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_holiday(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    holiday_data = Holiday.query.get_or_404(id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        holiday_date = request.form.get("date")
        holiday_type = request.form.get(
            "holiday_type",
            "Public"
        )

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not name or not holiday_date:

            flash(
                "Holiday name and date are required.",
                "danger"
            )

            return redirect(
                url_for(
                    "holiday.edit_holiday",
                    id=id
                )
            )

        try:

            holiday_date = datetime.strptime(
                holiday_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid holiday date.",
                "danger"
            )

            return redirect(
                url_for(
                    "holiday.edit_holiday",
                    id=id
                )
            )

        # ==========================
        # Duplicate Check
        # ==========================

        existing = Holiday.query.filter(
            Holiday.date == holiday_date,
            Holiday.id != id
        ).first()

        if existing:

            flash(
                "Another holiday already exists "
                "on this date.",
                "warning"
            )

            return redirect(
                url_for(
                    "holiday.edit_holiday",
                    id=id
                )
            )

        holiday_data.name = name
        holiday_data.date = holiday_date
        holiday_data.holiday_type = holiday_type
        holiday_data.description = description

        db.session.commit()

        flash(
            "Holiday updated successfully!",
            "success"
        )

        return redirect(
            url_for("holiday.holiday_list")
        )

    return render_template(
        "holiday/edit.html",
        holiday=holiday_data
    )


# ==========================
# Delete Holiday
# ==========================

@holiday.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_holiday(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    holiday_data = Holiday.query.get_or_404(id)

    db.session.delete(holiday_data)
    db.session.commit()

    flash(
        "Holiday deleted successfully!",
        "success"
    )

    return redirect(
        url_for("holiday.holiday_list")
    )