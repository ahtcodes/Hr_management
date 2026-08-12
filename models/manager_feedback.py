from extensions import db
from datetime import datetime


class ManagerFeedback(db.Model):

    __tablename__ = "manager_feedback"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    feedback = db.Column(
        db.Text,
        nullable=False
    )

    rating = db.Column(
        db.Float,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        backref="manager_feedbacks"
    )