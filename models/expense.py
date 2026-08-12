from extensions import db
from datetime import datetime


class Expense(db.Model):

    __tablename__ = "expenses"

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

    category = db.Column(
        db.String(100),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    expense_date = db.Column(
        db.Date,
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    receipt = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    approved_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    approved_at = db.Column(
        db.DateTime,
        nullable=True
    )

    reimbursement_status = db.Column(
        db.String(30),
        default="Pending"
    )

    reimbursed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    employee = db.relationship(
        "Employee",
        backref="expenses"
    )

    approver = db.relationship(
        "User",
        foreign_keys=[approved_by]
    )