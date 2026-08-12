from extensions import db


class Shift(db.Model):

    __tablename__ = "shifts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    shift_name = db.Column(
        db.String(100),
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    working_hours = db.Column(
        db.Float,
        default=8
    )


    # Employees under this shift
    employees = db.relationship(
        "Employee",
        back_populates="shift"
    )