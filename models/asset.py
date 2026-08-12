from extensions import db
from datetime import datetime


# ==========================================
# Asset Model
# ==========================================

class Asset(db.Model):

    __tablename__ = "assets"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    asset_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    asset_type = db.Column(
        db.String(50),
        nullable=False
    )

    asset_name = db.Column(
        db.String(150),
        nullable=False
    )

    brand = db.Column(
        db.String(100),
        nullable=True
    )

    model = db.Column(
        db.String(100),
        nullable=True
    )

    serial_number = db.Column(
        db.String(100),
        nullable=True
    )

    purchase_date = db.Column(
        db.Date,
        nullable=True
    )

    purchase_price = db.Column(
        db.Float,
        default=0
    )

    status = db.Column(
        db.String(30),
        default="Available"
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Asset Assignment History
    assignments = db.relationship(
        "AssetAssignment",
        backref="asset",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ==========================================
# Asset Assignment Model
# ==========================================

class AssetAssignment(db.Model):

    __tablename__ = "asset_assignments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    assigned_date = db.Column(
        db.Date,
        default=datetime.utcnow
    )

    returned_date = db.Column(
        db.Date,
        nullable=True
    )

    condition_on_assignment = db.Column(
        db.String(100),
        nullable=True
    )

    condition_on_return = db.Column(
        db.String(100),
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    employee = db.relationship(
        "Employee",
        backref="asset_assignments"
    )