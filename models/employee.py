from extensions import db


# ============================================================
# Department Model
# ============================================================

class Department(db.Model):

    __tablename__ = "departments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="Active"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    employees = db.relationship(
        "Employee",
        back_populates="department"
    )


# ============================================================
# Designation Model
# ============================================================

class Designation(db.Model):

    __tablename__ = "designations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="Active"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    employees = db.relationship(
        "Employee",
        back_populates="designation"
    )


# ============================================================
# Employee Model
# ============================================================

class Employee(db.Model):

    __tablename__ = "employees"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========================================================
    # Documents
    # ========================================================

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

    # ========================================================
    # Employee Code
    # ========================================================

    employee_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    # ========================================================
    # Biometric
    # ========================================================

    biometric_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    # ========================================================
    # Basic Information
    # ========================================================

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

    # ========================================================
    # Department Foreign Key
    # ========================================================

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=True
    )

    department = db.relationship(
        "Department",
        back_populates="employees"
    )

    # ========================================================
    # Designation Foreign Key
    # ========================================================

    designation_id = db.Column(
        db.Integer,
        db.ForeignKey("designations.id"),
        nullable=True
    )

    designation = db.relationship(
        "Designation",
        back_populates="employees"
    )

    # ========================================================
    # Employment Information
    # ========================================================

    joining_date = db.Column(
        db.Date,
        nullable=False
    )

    resignation_date = db.Column(
        db.Date,
        nullable=True
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

    # ========================================================
    # Salary
    # ========================================================

    basic_salary = db.Column(
        db.Float,
        nullable=False
    )

    overtime_rate = db.Column(
        db.Float,
        nullable=False
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

    # ========================================================
    # Shift Foreign Key
    # ========================================================

    shift_id = db.Column(
        db.Integer,
        db.ForeignKey("shifts.id")
    )

    # ========================================================
    # Shift Relationship
    # ========================================================

    shift = db.relationship(
        "Shift",
        back_populates="employees"
    )

    # ========================================================
    # Emergency Contact
    # ========================================================

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

    # ========================================================
    # User Relationship
    # ========================================================

    user = db.relationship(
    "User",
    back_populates="employee",
    uselist=False,
    cascade="all, delete-orphan"
)