from extensions import db
from datetime import datetime


class Evaluation(db.Model):

    __tablename__ = "evaluations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    review_period = db.Column(
        db.String(100),
        nullable=True
    )

    rating = db.Column(
        db.Float,
        default=0
    )

    strengths = db.Column(
        db.Text,
        nullable=True
    )

    weaknesses = db.Column(
        db.Text,
        nullable=True
    )

    comments = db.Column(
        db.Text,
        nullable=True
    )

    manager_feedback = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        backref="evaluations"
    )