from extensions import db
from datetime import datetime


class Notice(db.Model):

    __tablename__ = "notices"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    notice_type = db.Column(
        db.String(50),
        nullable=False
    )

    event_date = db.Column(
        db.Date,
        nullable=True
    )

    target_audience = db.Column(
        db.String(50),
        default="All"
    )

    status = db.Column(
        db.String(30),
        default="Published"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )