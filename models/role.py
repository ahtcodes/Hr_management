from extensions import db


# ==========================
# Role-Permission Association
# ==========================

role_permissions = db.Table(
    "role_permissions",

    db.Column(
        "role_id",
        db.Integer,
        db.ForeignKey("roles.id"),
        primary_key=True
    ),

    db.Column(
        "permission_id",
        db.Integer,
        db.ForeignKey("permissions.id"),
        primary_key=True
    )
)


# ==========================
# Role Model
# ==========================

class Role(db.Model):

    __tablename__ = "roles"

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

    permissions = db.relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

    users = db.relationship(
        "User",
        back_populates="role"
    )


# ==========================
# Permission Model
# ==========================

class Permission(db.Model):

    __tablename__ = "permissions"

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

    roles = db.relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )