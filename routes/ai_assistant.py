import os
import json

from dotenv import load_dotenv

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    abort,
    current_app
)

from flask_login import login_required, current_user
from groq import Groq

from models.employee import Employee, Department, Designation
from models.attendance import Attendance
from models.leave import Leave


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# BLUEPRINT
# =========================================================

ai_assistant = Blueprint(
    "ai_assistant",
    __name__,
    url_prefix="/ai-assistant"
)


# =========================================================
# ADMIN / HR ACCESS
# =========================================================

def admin_required():

    if not current_user.is_authenticated:
        abort(401)

    if not current_user.has_any_role(
        "Super Admin",
        "Admin",
        "HR Manager"
    ):
        abort(403)


# =========================================================
# GROQ CLIENT
# =========================================================

def get_groq_client():

    load_dotenv(override=True)

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured in .env"
        )

    return Groq(
        api_key=api_key
    )


# =========================================================
# GROQ MODEL
# =========================================================

def get_groq_model():

    load_dotenv(override=True)

    model = os.getenv("GROQ_MODEL")

    if not model:
        model = "openai/gpt-oss-20b"

    return model.strip()


# =========================================================
# PEOPLEdesk SYSTEM KNOWLEDGE
# =========================================================

def get_system_knowledge():

    return {
        "system_name": "PeopleDesk HR",

        "system_type": "Human Resource Management System",

        "description": (
            "PeopleDesk HR is a web-based Human Resource "
            "Management System used to manage employees, "
            "attendance, leaves, departments, designations, "
            "users, roles, permissions and HR information."
        ),

        "main_modules": [

            "Dashboard",

            "Employees",

            "Departments",

            "Designations",

            "Attendance",

            "Leaves",

            "Shifts",

            "Payroll and Salary",

            "Users",

            "Roles and Permissions",

            "Registration Requests",

            "Reports",

            "Notifications",

            "Employee Documents",

            "Employee Profile",

            "HR Management"
        ],

        "employee_features": [

            "Create employee records",

            "View employee records",

            "Edit employee information",

            "Employee profile management",

            "Employee code management",

            "Department assignment",

            "Designation assignment",

            "Joining date",

            "Resignation date",

            "Employment type",

            "Location",

            "Contact information",

            "Emergency contact information",

            "Salary information",

            "Employee documents",

            "Employee status"
        ],

        "attendance_features": [

            "Attendance records",

            "Employee attendance",

            "Attendance status",

            "Attendance history",

            "Attendance reporting"
        ],

        "leave_features": [

            "Leave records",

            "Employee leave management",

            "Leave requests",

            "Leave status",

            "Leave history",

            "Leave reporting"
        ],

        "organization_features": [

            "Departments",

            "Designations",

            "Employee department assignment",

            "Employee designation assignment",

            "Organization structure"
        ],

        "user_management": [

            "User accounts",

            "User roles",

            "Role based access",

            "Permissions",

            "Registration requests",

            "User approval",

            "User status"
        ],

        "known_roles": [

            "Super Admin",

            "HR Manager",

            "Department Manager",

            "Employee"
        ],

        "access_rules": {

            "Super Admin": (
                "Highest level system access. "
                "Can manage system administration, "
                "users, roles and permissions."
            ),

            "HR Manager": (
                "HR management access including "
                "employee and HR related operations "
                "according to assigned permissions."
            ),

            "Department Manager": (
                "Department related management according "
                "to assigned permissions."
            ),

            "Employee": (
                "Employee-level access to the features "
                "allowed by the system."
            )
        },

        "ai_capabilities": [

            "Explain PeopleDesk HR features",

            "Explain how a system feature works",

            "Answer questions about HR concepts",

            "Answer questions about available HR data",

            "Explain employee management",

            "Explain attendance management",

            "Explain leave management",

            "Explain departments and designations",

            "Explain users, roles and permissions",

            "Explain HR workflows",

            "Explain reports",

            "Help users understand the system",

            "Analyze available HR statistics",

            "Answer in English",

            "Answer in Roman Urdu"
        ],

        "ai_restrictions": [

            "Cannot create database records",

            "Cannot update database records",

            "Cannot delete database records",

            "Cannot approve records",

            "Cannot reject records",

            "Cannot change employee salary",

            "Cannot change user passwords",

            "Cannot change permissions",

            "Cannot expose passwords",

            "Cannot expose API keys",

            "Cannot expose authentication secrets",

            "Cannot expose private credentials"
        ]
    }


# =========================================================
# HR DATABASE CONTEXT
# =========================================================

def get_hr_context():

    try:

        # =====================================================
        # BASIC COUNTS
        # =====================================================

        total_employees = Employee.query.count()

        active_employees = Employee.query.filter_by(
            status="Active"
        ).count()

        inactive_employees = Employee.query.filter(
            Employee.status != "Active"
        ).count()

        total_departments = Department.query.count()

        total_designations = Designation.query.count()

        total_attendance = Attendance.query.count()

        total_leaves = Leave.query.count()


        # =====================================================
        # EMPLOYEE DATA
        # =====================================================

        employees = Employee.query.order_by(
            Employee.full_name
        ).limit(200).all()

        employee_data = []

        for employee in employees:

            department_name = (
                employee.department.name
                if employee.department
                else "Not Assigned"
            )

            designation_name = (
                employee.designation.name
                if employee.designation
                else "Not Assigned"
            )

            employee_data.append({

                "employee_code": employee.employee_code,

                "name": employee.full_name,

                "email": employee.email,

                "phone": employee.phone,

                "department": department_name,

                "designation": designation_name,

                "status": employee.status,

                "employment_type": employee.employment_type,

                "location": employee.location,

                "joining_date": (
                    employee.joining_date.isoformat()
                    if employee.joining_date
                    else None
                ),

                "resignation_date": (
                    employee.resignation_date.isoformat()
                    if employee.resignation_date
                    else None
                )
            })


        # =====================================================
        # RETURN HR DATA
        # =====================================================

        return {

            "statistics": {

                "total_employees": total_employees,

                "active_employees": active_employees,

                "inactive_employees": inactive_employees,

                "departments": total_departments,

                "designations": total_designations,

                "attendance_records": total_attendance,

                "leave_records": total_leaves
            },

            "employees": employee_data
        }


    except Exception as e:

        current_app.logger.exception(
            "Could not load HR context"
        )

        return {

            "statistics": {},

            "employees": [],

            "error": str(e)
        }


# =========================================================
# AI SYSTEM PROMPT
# =========================================================

def build_system_prompt(
    hr_context,
    system_knowledge
):

    return f"""
You are PeopleDesk AI Assistant.

=========================================================
YOUR IDENTITY
=========================================================

You are the official AI assistant inside:

PeopleDesk HR

PeopleDesk HR is a Human Resource Management System.

Your job is to help administrators and HR users
understand and use the PeopleDesk HR system.

You should behave like a knowledgeable HR software
assistant.

=========================================================
WHAT YOU CAN ANSWER
=========================================================

You can answer questions about ANY relevant part of
PeopleDesk HR.

This includes:

1. Employees
2. Employee profiles
3. Employee documents
4. Departments
5. Designations
6. Attendance
7. Leaves
8. Shifts
9. Payroll
10. Salary
11. Users
12. Roles
13. Permissions
14. Registration Requests
15. Notifications
16. Reports
17. Dashboard
18. HR processes
19. Recruitment concepts
20. Employee management
21. Attendance concepts
22. Leave concepts
23. Basic payroll concepts
24. HR management concepts
25. How to use PeopleDesk HR
26. What a particular module does
27. What a particular role can do
28. General questions about the HR system

=========================================================
SYSTEM KNOWLEDGE
=========================================================

{json.dumps(system_knowledge, indent=2)}


=========================================================
CURRENT DATABASE DATA
=========================================================

The following information comes from the current
PeopleDesk HR database.

IMPORTANT:

Use this information when the user asks about actual
company/HR data.

Statistics:

{json.dumps(
    hr_context.get("statistics", {}),
    indent=2
)}


Employee Data:

{json.dumps(
    hr_context.get("employees", []),
    indent=2
)}


=========================================================
HOW TO ANSWER SYSTEM QUESTIONS
=========================================================

If the user asks:

"PeopleDesk HR kya hai?"

Explain the PeopleDesk HR system.

If the user asks:

"Employee add kaise karte hain?"

Explain the employee management process.

If the user asks:

"Roles kya hain?"

Explain the roles available in the system.

If the user asks:

"Super Admin kya kar sakta hai?"

Explain the known Super Admin capabilities.

If the user asks:

"HR Manager kya kar sakta hai?"

Explain HR Manager access according to the
known system permissions.

If the user asks:

"Hamare kitne employees hain?"

Use the actual database statistics.

If the user asks:

"Ali kis department mein hai?"

Search the provided employee data.

If the requested employee exists in the provided data,
give the available information.

If the employee is not available in the provided data,
clearly say:

"Is employee ki information current AI data mein
available nahi hai."

=========================================================
IMPORTANT DATA RULE
=========================================================

Never invent company data.

Never guess an employee's:

- Salary
- Attendance
- Leave
- Department
- Designation
- Email
- Phone
- Status
- Joining date
- Resignation date

unless the information is available in the provided
database context.

For general HR knowledge, you may provide normal
professional HR guidance.

For PeopleDesk-specific functionality, use the
PeopleDesk system knowledge provided above.

=========================================================
LANGUAGE
=========================================================

If the user asks in English:

Answer in English.

If the user asks in Roman Urdu:

Answer in simple Roman Urdu.

If the user mixes English and Roman Urdu:

You may use a natural mixture.

Keep answers easy to understand.

=========================================================
SECURITY
=========================================================

NEVER reveal:

- Passwords
- Password hashes
- API keys
- Secret keys
- Authentication tokens
- Private credentials
- Internal security secrets

Never provide sensitive authentication information.

=========================================================
DATABASE ACCESS
=========================================================

You are READ-ONLY.

You can analyze the data supplied to you.

You CANNOT:

- Create records
- Update records
- Delete records
- Approve records
- Reject records
- Change salaries
- Change passwords
- Change permissions
- Modify employee records
- Modify attendance
- Modify leaves

If the user asks you to modify data, clearly explain
that you are currently a read-only assistant.

=========================================================
ANSWER STYLE
=========================================================

Be professional.

Be helpful.

Be concise.

If the question requires steps, provide numbered steps.

If the question is simple, give a simple answer.

Do not unnecessarily mention technical implementation.

Do not say that you have database access beyond the
data supplied in the current context.

=========================================================
"""


# =========================================================
# AI HOME PAGE
# =========================================================

@ai_assistant.route("/")
@login_required
def index():

    admin_required()

    return render_template(
        "ai_assistant.html"
    )


# =========================================================
# CHAT API
# =========================================================

@ai_assistant.route(
    "/chat",
    methods=["POST"]
)
@login_required
def chat():

    admin_required()

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "success": False,

            "message": "Invalid request."

        }), 400


    user_message = (
        data.get("message") or ""
    ).strip()


    if not user_message:

        return jsonify({

            "success": False,

            "message": "Please enter a message."

        }), 400


    if len(user_message) > 4000:

        return jsonify({

            "success": False,

            "message": "Message is too long."

        }), 400


    try:

        # =====================================================
        # GET CURRENT HR DATABASE DATA
        # =====================================================

        hr_context = get_hr_context()


        # =====================================================
        # GET SYSTEM KNOWLEDGE
        # =====================================================

        system_knowledge = (
            get_system_knowledge()
        )


        # =====================================================
        # BUILD SYSTEM PROMPT
        # =====================================================

        system_prompt = build_system_prompt(

            hr_context,

            system_knowledge

        )


        # =====================================================
        # GET CHAT HISTORY
        # =====================================================

        history = session.get(

            "ai_chat_history",

            []

        )


        if not isinstance(
            history,
            list
        ):

            history = []


        messages = [

            {

                "role": "system",

                "content": system_prompt

            }

        ]


        # =====================================================
        # ADD PREVIOUS CHAT HISTORY
        # =====================================================

        for message in history[-10:]:

            if not isinstance(
                message,
                dict
            ):

                continue


            role = message.get(
                "role"
            )

            content = message.get(
                "content"
            )


            if role in [

                "user",

                "assistant"

            ] and content:

                messages.append({

                    "role": role,

                    "content": str(
                        content
                    )

                })


        # =====================================================
        # CURRENT QUESTION
        # =====================================================

        messages.append({

            "role": "user",

            "content": user_message

        })


        # =====================================================
        # GROQ CLIENT
        # =====================================================

        client = get_groq_client()

        model = get_groq_model()


        current_app.logger.info(

            "PeopleDesk AI using Groq model: %s",

            model

        )


        # =====================================================
        # SEND REQUEST TO GROQ
        # =====================================================

        completion = client.chat.completions.create(

            model=model,

            messages=messages,

            temperature=0.3,

            max_tokens=1500

        )


        # =====================================================
        # GET AI RESPONSE
        # =====================================================

        assistant_message = (

            completion

            .choices[0]

            .message

            .content

        )


        if not assistant_message:

            assistant_message = (

                "Sorry, mujhe response generate "
                "nahi ho saka."

            )


        assistant_message = str(

            assistant_message

        ).strip()


        # =====================================================
        # SAVE CHAT HISTORY
        # =====================================================

        history.append({

            "role": "user",

            "content": user_message

        })


        history.append({

            "role": "assistant",

            "content": assistant_message

        })


        # Keep only last 20 messages

        session["ai_chat_history"] = (

            history[-20:]

        )

        session.modified = True


        # =====================================================
        # SUCCESS RESPONSE
        # =====================================================

        return jsonify({

            "success": True,

            "message": assistant_message

        })


    except Exception as e:

        # =====================================================
        # LOG REAL ERROR
        # =====================================================

        current_app.logger.exception(

            "PeopleDesk AI Assistant error: %s",

            str(e)

        )


        return jsonify({

            "success": False,

            "message": (

                "AI Assistant error: "

                + str(e)

            )

        }), 500


# =========================================================
# CLEAR CHAT
# =========================================================

@ai_assistant.route(

    "/clear",

    methods=["POST"]

)
@login_required
def clear_chat():

    admin_required()


    session.pop(

        "ai_chat_history",

        None

    )


    return jsonify({

        "success": True

    })
