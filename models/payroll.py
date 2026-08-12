from extensions import db
from datetime import datetime


class Payroll(db.Model):

    __tablename__ = "payrolls"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    month = db.Column(
        db.String(20),
        nullable=False
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    basic_salary = db.Column(
        db.Float,
        nullable=False
    )

    present_days = db.Column(
        db.Integer,
        default=0
    )

    absent_days = db.Column(
        db.Integer,
        default=0
    )

    overtime_hours = db.Column(
        db.Float,
        default=0
    )

    overtime_pay = db.Column(
        db.Float,
        default=0
    )

    bonus = db.Column(
        db.Float,
        default=0
    )
    allowances = db.Column(
        db.Float,
        default=0
    )

    tax = db.Column(
        db.Float,
        default=0
    )

    security_deduction = db.Column(
        db.Float,
        default=0
    )

    deductions = db.Column(
        db.Float,
        default=0
    )

    net_salary = db.Column(
        db.Float,
        default=0
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    late_deduction = db.Column(
        db.Float,
        default=0
    )

    absence_deduction = db.Column(
        db.Float,
        default=0
    )

    leave_days = db.Column(
        db.Integer,
        default=0
    )

    final_salary = db.Column(
        db.Float,
        default=0
    )

    total_working_hours = db.Column(
        db.Float,
        default=0
    )

    hourly_rate = db.Column(
        db.Float,
        default=0
    )

    daily_rate = db.Column(
        db.Float,
        default=0
    )

    working_days = db.Column(
        db.Integer,
        default=0
    )

    # JSON string storing per-day attendance breakdown for the month
    # Format: [{date, day, status, check_in, check_out, working_hours,
    #           late_hours, early_leave_hours, overtime_hours}]
    daily_breakdown = db.Column(
        db.Text,
        default="[]"
    )

    employee = db.relationship(
        "Employee",
        backref="payrolls"
    )

