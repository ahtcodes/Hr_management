from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models.notice import Notice
from extensions import db
from datetime import datetime
from models.document import Document

notice = Blueprint(
    "notice",
    __name__,
    url_prefix="/notices"
)


# ==========================
# Notices List
# ==========================

@notice.route("/")
@login_required
def notice_list():

    notices = Notice.query.order_by(
        Notice.created_at.desc()
    ).all()

    documents = []

    # Employee ke liye documents
    if current_user.employee:

        documents = Document.query.filter(
            db.or_(
                Document.employee_id == current_user.employee.id,
                Document.document_type == "Company Policy"
            )
        ).order_by(
            Document.uploaded_at.desc()
        ).all()

    return render_template(
        "notice/list.html",
        notices=notices,
        documents=documents
    )

# ==========================
# Create Notice
# ==========================

@notice.route("/create", methods=["GET", "POST"])
@login_required
def create_notice():

    if not current_user.has_any_role("Super Admin""HR Manager"):
        abort(403)

    if request.method == "POST":

        title = request.form.get("title")
        description = request.form.get("description")
        notice_type = request.form.get("notice_type")
        event_date = request.form.get("event_date")
        target_audience = request.form.get("target_audience") or "All"

        parsed_date = None

        if event_date:
            try:
                parsed_date = datetime.strptime(
                    event_date,
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                flash("Invalid date.", "danger")
                return redirect(
                    url_for("notice.create_notice")
                )

        new_notice = Notice(
            title=title,
            description=description,
            notice_type=notice_type,
            event_date=parsed_date,
            target_audience=target_audience,
            status="Published"
        )

        db.session.add(new_notice)
        db.session.commit()

        flash(
            "Notice created successfully!",
            "success"
        )

        return redirect(
            url_for("notice.notice_list")
        )

    return render_template(
        "notice/create.html"
    )


# ==========================
# Delete Notice
# ==========================

@notice.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_notice(id):

    if not current_user.has_any_role("Super Admin", "HR Manager"):
        abort(403)

    notice_data = Notice.query.get_or_404(id)

    db.session.delete(notice_data)
    db.session.commit()

    flash(
        "Notice deleted successfully!",
        "success"
    )

    return redirect(
        url_for("notice.notice_list")
    )