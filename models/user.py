from extensions import db
from flask_login import UserMixin


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    # Role Foreign Key
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=True
    )

    # Role Relationship
    role = db.relationship(
        "Role",
        back_populates="users"
    )

    # Account Status
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    # Foreign Key to Employee table
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=True
    )

    # One-to-One Relationship
    employee = db.relationship(
        "Employee",
        back_populates="user",
        uselist=False
    )

    def has_role(self, role_name):
        if not self.role:
            return False

        user_role = self.role.name.strip().lower()
        required_role = role_name.strip().lower()

        if user_role == required_role:
            return True

            # Super Admin ko admin-level access
        if user_role == "super admin" and required_role == "admin":
            return True
            
        return False

    @property
    def is_admin(self):
        return self.role and self.role.name in [
            "Super Admin",
            "admin"
        ]

    @property
    def is_employee(self):
        return self.role and self.role.name == "Employee"

    @property
    def is_approved(self):
        return self.status == "approved"