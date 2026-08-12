from extensions import db
from datetime import datetime


class Holiday(db.Model):

    __tablename__ = "holidays"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

    holiday_type = db.Column(
        db.String(30),
        nullable=False,
        default="Public"
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(20),
        default="Active"
    )

    def __repr__(self):
        return f"<Holiday {self.name} - {self.date}>"