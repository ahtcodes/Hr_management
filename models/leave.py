from extensions import db
from datetime import datetime


class Leave(db.Model):

    __tablename__ = "leaves"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    leave_type = db.Column(
        db.String(50),
        nullable=False,
        default="Annual"
    )

    start_date = db.Column(db.Date, nullable=False)

    end_date = db.Column(db.Date, nullable=False)

    total_days = db.Column(db.Integer, nullable=False, default=1)

    reason = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

    remarks = db.Column(db.Text, nullable=True)

    applied_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    employee = db.relationship("Employee", backref="leaves")

