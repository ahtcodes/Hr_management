"""Sync the database schema with the models.

This script adds the missing columns and tables to the existing
instance/database.db so that all features (including employee
self-attendance) work correctly.

Run:  python migrate_db.py
"""
import sqlite3

DB_PATH = "instance/database.db"


def get_columns(conn, table):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in c.fetchall()}


def get_tables(conn):
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in c.fetchall()}


def add_column(conn, table, column, definition):
    c = conn.cursor()
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()
        print(f"  + Added {table}.{column}")
    except sqlite3.OperationalError as e:
        print(f"  - {table}.{column} already exists or error: {e}")


def main():
    conn = sqlite3.connect(DB_PATH)
    tables = get_tables(conn)

    # -------------------------
    # 1. ATTENDANCE table
    # -------------------------
    print("=== attendance table ===")
    att_cols = get_columns(conn, "attendance")

    if "shift_start" not in att_cols:
        add_column(conn, "attendance", "shift_start", "TIME")
    if "shift_end" not in att_cols:
        add_column(conn, "attendance", "shift_end", "TIME")
    if "late_hours" not in att_cols:
        add_column(conn, "attendance", "late_hours", "FLOAT DEFAULT 0")
    if "early_leave_hours" not in att_cols:
        add_column(conn, "attendance", "early_leave_hours", "FLOAT DEFAULT 0")
    if "late_deduction" not in att_cols:
        add_column(conn, "attendance", "late_deduction", "FLOAT DEFAULT 0")
    if "deduction_approved" not in att_cols:
        add_column(conn, "attendance", "deduction_approved", "BOOLEAN DEFAULT 0")
    if "final_salary" not in att_cols:
        add_column(conn, "attendance", "final_salary", "FLOAT DEFAULT 0")

    # -------------------------
    # 2. SHIFTS table
    # -------------------------
    print("=== shifts table ===")
    if "shifts" not in tables:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE shifts (
                id INTEGER PRIMARY KEY,
                shift_name VARCHAR(100) NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                working_hours FLOAT DEFAULT 8
            )
        """)
        conn.commit()
        print("  + Created shifts table")
    else:
        print("  - shifts table already exists")

    # -------------------------
    # 3. EMPLOYEES table
    # -------------------------
    print("=== employees table ===")
    emp_cols = get_columns(conn, "employees")

    if "shift_id" not in emp_cols:
        add_column(conn, "employees", "shift_id", "INTEGER")

    # -------------------------
    # 4. USERS table
    # -------------------------
    print("=== users table ===")
    usr_cols = get_columns(conn, "users")

    if "status" not in usr_cols:
        add_column(conn, "users", "status", "VARCHAR(20) DEFAULT 'pending'")
    if "employee_id" not in usr_cols:
        add_column(conn, "users", "employee_id", "INTEGER")

    conn.close()
    print("\nDatabase schema sync complete.")


if __name__ == "__main__":
    main()
