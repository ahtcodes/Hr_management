from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models.asset import Asset


asset = Blueprint(
    "asset",
    __name__,
    url_prefix="/assets"
)


@asset.route("")
@login_required
def asset_list():

    # Super Admin + Employee can VIEW assets
    if not (
        current_user.has_role("Super Admin")
        or current_user.has_role("Employee")
    ):
        abort(403)

    assets = Asset.query.order_by(
        Asset.created_at.desc()
    ).all()

    return render_template(
        "assets/list.html",
        assets=assets
    )

# ==========================
# Create Asset
# ==========================

@asset.route("/create", methods=["GET", "POST"])
@login_required
def create_asset():

    if not current_user.has_role("Super Admin"):
        abort(403)

    if request.method == "POST":

        asset_code = request.form.get("asset_code")
        asset_type = request.form.get("asset_type")
        asset_name = request.form.get("asset_name")
        brand = request.form.get("brand")
        model = request.form.get("model")
        serial_number = request.form.get("serial_number")
        purchase_date = request.form.get("purchase_date")
        purchase_price = request.form.get("purchase_price") or 0
        description = request.form.get("description")

        new_asset = Asset(
            asset_code=asset_code,
            asset_type=asset_type,
            asset_name=asset_name,
            brand=brand,
            model=model,
            serial_number=serial_number,
            purchase_price=float(purchase_price),
            description=description
        )

        if purchase_date:
            from datetime import datetime

            new_asset.purchase_date = datetime.strptime(
                purchase_date,
                "%Y-%m-%d"
            ).date()

        db.session.add(new_asset)
        db.session.commit()

        flash(
            "Asset created successfully!",
            "success"
        )

        return redirect(
            url_for("asset.asset_list")
        )

    return render_template(
        "assets/create.html"
    )


# ==========================
# Delete Asset
# ==========================

@asset.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_asset(id):

    if not current_user.has_role("Super Admin"):
        abort(403)

    asset_data = Asset.query.get_or_404(id)

    db.session.delete(asset_data)
    db.session.commit()

    flash(
        "Asset deleted successfully!",
        "success"
    )

    return redirect(
        url_for("asset.asset_list")
    )