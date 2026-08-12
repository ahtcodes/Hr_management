from extensions import db


class Employee(db.Model):

    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)

    # Documents

    profile_photo = db.Column(
        db.String(255),
        nullable=True
    )

    cnic_file = db.Column(
        db.String(255),
        nullable=True
    )

    cv_file = db.Column(
        db.String(255),
        nullable=True
    )

    certificate_file = db.Column(
        db.String(255),
        nullable=True
    )

    # Emergency Contact

    emergency_contact_name = db.Column(
        db.String(100),
        nullable=True
    )

    emergency_contact_relation = db.Column(
        db.String(50),
        nullable=True
    )

    emergency_contact_phone = db.Column(
        db.String(20),
        nullable=True
    )

    employee_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )
    biometric_id = db.Column(
    db.String(50),
    unique=True,
    nullable=True
    )

    full_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=False
    )

    designation = db.Column(
        db.String(100),
        nullable=False
    )

    joining_date = db.Column(
        db.Date,
        nullable=False
    )
    resignation_date = db.Column(
    db.Date,
    nullable=True
    )

    basic_salary = db.Column(
        db.Float,
        nullable=False
    )

    overtime_rate = db.Column(
        db.Float,
        nullable=False
    )

    
    employment_type = db.Column(
    db.String(20),
    nullable=False,
    default="Full Time"
    )

    location = db.Column(
    db.String(100),
    nullable=False,
    default="Faisalabad"
    )


    status = db.Column(
        db.String(20),
        default="Active"
    )


    # Shift Foreign Key
    shift_id = db.Column(
        db.Integer,
        db.ForeignKey("shifts.id")
    )


    # Shift Relationship
    shift = db.relationship(
        "Shift",
        back_populates="employees"
    )


    # User Relationship
    user = db.relationship(
        "User",
        back_populates="employee",
        uselist=False
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

profile_photo = db.Column(
    db.String(255),
    nullable=True
)

cnic_file = db.Column(
    db.String(255),
    nullable=True
)

cv_file = db.Column(
    db.String(255),
    nullable=True
)

certificate_file = db.Column(
    db.String(255),
    nullable=True
)
