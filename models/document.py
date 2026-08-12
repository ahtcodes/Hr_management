from extensions import db
from datetime import datetime


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Employee
    # Company Policy ke liye employee_id NULL ho sakta hai
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=True
    )

    # Document title
    title = db.Column(
        db.String(200),
        nullable=False
    )

    # Contract / Offer Letter / Appointment Letter /
    # Experience Letter / Company Policy
    document_type = db.Column(
        db.String(50),
        nullable=False
    )

    # Actual uploaded file name
    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    # File location
    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    # User who uploaded the document
    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Employee relationship
    employee = db.relationship(
        "Employee",
        backref="managed_documents"
    )

    def __repr__(self):
        return f"<Document {self.title}>"