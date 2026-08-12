from flask import Flask, render_template
from flask_login import login_required
from flask import send_from_directory

from extensions import db, login_manager, bcrypt, migrate

from models.shift import Shift
from models.user import User
from models.holiday import Holiday
from models.evaluation import Evaluation
from models.kpi import KPI
from models.role import Role, Permission
from models.manager_feedback import ManagerFeedback
from models.asset import Asset, AssetAssignment
from models.notice import Notice
from models.expense import Expense

from routes.expense import expense
from routes.attendance import attendance
from routes.notice import notice
from routes.auth import auth
from routes.manager_feedback import manager_feedback
from routes.employee import employee
from routes.leave import leave
from routes.admin import admin
from routes.payroll import payroll
from routes.goal import goal
from routes.holiday import holiday
from routes.kpi import kpi
from routes.evaluation import evaluation
from routes.asset import asset
from config import Config

app = Flask(__name__)


# =======================
# Load Configuration
# =======================
app.config.from_object(Config)

import os

folders = [
    os.path.join(app.config["UPLOAD_FOLDER"], "photos"),
    os.path.join(app.config["UPLOAD_FOLDER"], "cnic"),
    os.path.join(app.config["UPLOAD_FOLDER"], "cv"),
    os.path.join(app.config["UPLOAD_FOLDER"], "certificates")
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)


# =========================
# Initialize Extensions
# =========================
db.init_app(app)
login_manager.init_app(app)
bcrypt.init_app(app)
migrate.init_app(app, db)

# ==========================
# Register Blueprints
# ==========================
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(employee)
app.register_blueprint(attendance)
app.register_blueprint(leave)
app.register_blueprint(payroll)
app.register_blueprint(holiday)
app.register_blueprint(kpi)
app.register_blueprint(evaluation)
app.register_blueprint(goal)
app.register_blueprint(manager_feedback)
app.register_blueprint(asset)
app.register_blueprint(notice)
app.register_blueprint(expense)

# =========================
# Flask Login Configuration
# =========================
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ===========================
# Home Route
# ===========================
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/uploads/<folder>/<filename>")
def uploaded_file(folder, filename):
    return send_from_directory(
        os.path.join(app.config["UPLOAD_FOLDER"], folder),
        filename
    )


# =========================
# Create Database Tables
# ========================= 
with app.app_context():

    db.create_all()

    # ==========================
    # Create Default Roles
    # ==========================

    default_roles = [
        ("Super Admin", "Full system access"),
        ("HR Manager", "Manage HR operations"),
        ("Department Manager", "Manage department employees"),
        ("Employee", "Employee self-service access")
    ]

    for role_name, description in default_roles: 

        existing_role = Role.query.filter_by(
            name=role_name
        ).first()

        if not existing_role:

            new_role = Role(
                name=role_name,
                description=description
            )

            db.session.add(new_role)

    db.session.commit()


# =========================
# Run Application
# =========================
if __name__ == "__main__":
    app.run(debug=True)