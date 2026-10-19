from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from flask_login import (
    login_required,
    current_user
)

from flask_socketio import (
    emit,
    join_room
)

from extensions import (
    db,
    socketio
)

from models.user import User
from models.employee import Employee
from models.chat import Conversation, Message

chat = Blueprint("chat", __name__, url_prefix="/chat")


# =========================================================
# CHAT HOME
# =========================================================
@chat.route("/")
@login_required
def chat_home():

    # Current user's conversations
    conversations = Conversation.query.filter(
        (Conversation.user1_id == current_user.id) |
        (Conversation.user2_id == current_user.id)
    ).order_by(
        Conversation.created_at.desc()
    ).all()

    # All other users for starting a new chat
    users = User.query.filter(
        User.id != current_user.id
    ).all()

    return render_template(
        "chat/chat.html",
        users=users,
        conversations=conversations
    )
# =========================================================
# SEARCH EMPLOYEES
# =========================================================

@chat.route("/search")
@login_required
def search_users():

    query = request.args.get(
        "q",
        ""
    ).strip()


    if not query:
        return jsonify([])


    users = (
        User.query
        .join(
            Employee,
            User.employee_id == Employee.id
        )
        .filter(
            User.id != current_user.id
        )
        .filter(
            User.status == "approved"
        )
        .filter(
            db.or_(
                Employee.full_name.ilike(
                    f"%{query}%"
                ),

                Employee.employee_code.ilike(
                    f"%{query}%"
                ),

                User.username.ilike(
                    f"%{query}%"
                )
            )
        )
        .limit(10)
        .all()
    )


    results = []


    for user in users:

        employee = user.employee


        results.append({

            "id": user.id,

            "username": user.username,

            "full_name":
                employee.full_name
                if employee
                else user.username,

            "employee_code":
                employee.employee_code
                if employee
                else "",

            "profile_photo":
                employee.profile_photo
                if employee
                else None

        })


    return jsonify(results)

# =========================================================
# START CHAT
# =========================================================

@chat.route("/start/<int:user_id>")
@login_required
def start_chat(user_id):

    if user_id == current_user.id:
        flash(
            "You cannot start a chat with yourself.",
            "danger"
        )

        return redirect(
            url_for("chat.chat_home")
        )

    other_user = User.query.get_or_404(user_id)

    # Check existing conversation
    conversation = Conversation.query.filter(
        (
            (Conversation.user1_id == current_user.id) &
            (Conversation.user2_id == other_user.id)
        )
        |
        (
            (Conversation.user1_id == other_user.id) &
            (Conversation.user2_id == current_user.id)
        )
    ).first()

    # Create conversation if it doesn't exist
    if not conversation:

        conversation = Conversation(
            user1_id=current_user.id,
            user2_id=other_user.id
        )

        db.session.add(conversation)
        db.session.commit()

    return redirect(
        url_for(
            "chat.conversation",
            conversation_id=conversation.id
        )
    )



# =========================================================
# OPEN CONVERSATION
# =========================================================

@chat.route("/<int:conversation_id>")
@login_required
def conversation(conversation_id):

    conversation = Conversation.query.get_or_404(
        conversation_id
    )

    # Security check
    if current_user.id not in [
        conversation.user1_id,
        conversation.user2_id
    ]:
        return "Unauthorized", 403

    messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(
        Message.created_at.asc()
    ).all()

    # Mark received messages as read
    for message in messages:

        if message.receiver_id == current_user.id:
            message.is_read = True

    db.session.commit()

    # Find other user
    if conversation.user1_id == current_user.id:
        other_user = conversation.user2
    else:
        other_user = conversation.user1

    return render_template(
        "chat/conversation.html",
        conversation=conversation,
        messages=messages,
        other_user=other_user
    )


# =========================================================
# SOCKETIO - JOIN CONVERSATION
# =========================================================

@socketio.on("join_chat")
def handle_join_chat(data):

    conversation_id = data.get("conversation_id")

    if not conversation_id:
        return

    conversation = Conversation.query.get(
        int(conversation_id)
    )

    if not conversation:
        return

    # Security check
    if current_user.id not in [
        conversation.user1_id,
        conversation.user2_id
    ]:
        return

    room = f"conversation_{conversation.id}"

    join_room(room)

    emit(
        "chat_joined",
        {
            "message": "Connected to chat"
        }
    )


# =========================================================
# SOCKETIO - SEND MESSAGE
# =========================================================

@socketio.on("send_message")
def handle_send_message(data):

    conversation_id = data.get("conversation_id")
    message_text = data.get("message", "").strip()

    if not conversation_id or not message_text:
        return

    conversation = Conversation.query.get(
        int(conversation_id)
    )

    if not conversation:
        return

    # Security check
    if current_user.id not in [
        conversation.user1_id,
        conversation.user2_id
    ]:
        return

    # Determine receiver
    if conversation.user1_id == current_user.id:

        receiver_id = conversation.user2_id

    else:

        receiver_id = conversation.user1_id

    # Save message in database
    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message_text,
        is_read=False
    )

    db.session.add(message)
    db.session.commit()

    # Send message to both users in room
    room = f"conversation_{conversation.id}"

    emit(
        "new_message",
        {
            "id": message.id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "message": message.message,
            "created_at": message.created_at.strftime(
                "%I:%M %p"
            )
        },
        room=room
    )