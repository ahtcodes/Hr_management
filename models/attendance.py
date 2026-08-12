from extensions import db
from datetime import datetime


class Attendance(db.Model):

    __tablename__ = "attendance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Employee Foreign Key
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    # Shift Foreign Key
    shift_id = db.Column(
        db.Integer,
        db.ForeignKey("shifts.id"),
        nullable=True
    )

    # Date
    date = db.Column(
        db.Date,
        default=datetime.utcnow().date()
    )

    # Attendance Status
    status = db.Column(
        db.String(20),
        nullable=False
    )

    # Check In / Check Out
    check_in = db.Column(
        db.Time
    )

    check_out = db.Column(
        db.Time
    )

    # Shift Timing Snapshot
    shift_start = db.Column(
        db.Time
    )

    shift_end = db.Column(
        db.Time
    )

    # Working Hours
    working_hours = db.Column(
        db.Float,
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

    # Late / Early Leave
    late_hours = db.Column(
        db.Float,
        default=0
    )

    early_leave_hours = db.Column(
        db.Float,
        default=0
    )
    # Paid / Unpaid Control
    late_paid = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    early_leave_paid = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # Salary
    late_deduction = db.Column(
        db.Float,
        default=0
    )

    deduction_approved = db.Column(
        db.Boolean,
        default=False
    )

    final_salary = db.Column(
        db.Float,
        default=0
    )

    # Relationships

    employee = db.relationship(
        "Employee",
        backref="attendance"
    )

    shift = db.relationship(
        "Shift",
        backref="attendances"
    )