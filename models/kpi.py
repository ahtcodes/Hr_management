from extensions import db
from datetime import datetime


class KPI(db.Model):

    __tablename__ = "kpis"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    target = db.Column(
        db.Float,
        default=0
    )

    achieved = db.Column(
        db.Float,
        default=0
    )

    unit = db.Column(
        db.String(50),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    start_date = db.Column(
        db.Date,
        nullable=True
    )

    end_date = db.Column(
        db.Date,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        backref="kpis"
    )