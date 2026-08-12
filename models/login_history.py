from extensions import db
from datetime import datetime


class LoginHistory(db.Model):

    __tablename__ = "login_history"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    username = db.Column(
        db.String(120),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False
    )

    ip_address = db.Column(
        db.String(50),
        nullable=True
    )

    login_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="login_history"
    )