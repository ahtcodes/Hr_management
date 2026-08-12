from flask import request
from flask_login import current_user

from extensions import db
from models.activity_log import ActivityLog


def log_activity(action, module=None):

    user_id = None

    if current_user.is_authenticated:
        user_id = current_user.id

    ip_address = request.remote_addr

    activity = ActivityLog(
        user_id=user_id,
        action=action,
        module=module,
        ip_address=ip_address
    )

    db.session.add(activity)
    db.session.commit()