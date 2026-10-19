"""Add department and designation management

Revision ID: 0fff2eff5cbb
Revises: 99e4139f0521
Create Date: 2026-08-13 12:26:07.341944

"""

from alembic import op
import sqlalchemy as sa


revision = "0fff2eff5cbb"
down_revision = "99e4139f0521"
branch_labels = None
depends_on = None


def upgrade():

    connection = op.get_bind()

    # =========================================================
    # 1. Create departments table if it does not exist
    # =========================================================

    connection.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(255),
            status VARCHAR(20) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))

    # =========================================================
    # 2. Create designations table if it does not exist
    # =========================================================

    connection.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS designations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(255),
            status VARCHAR(20) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))

    # =========================================================
    # 3. Add department_id and designation_id
    # =========================================================

    connection.execute(sa.text("""
        ALTER TABLE employees
        ADD COLUMN IF NOT EXISTS department_id INTEGER
    """))

    connection.execute(sa.text("""
        ALTER TABLE employees
        ADD COLUMN IF NOT EXISTS designation_id INTEGER
    """))

    # =========================================================
    # 4. Copy old departments
    # =========================================================

    connection.execute(sa.text("""
        INSERT INTO departments (name)
        SELECT DISTINCT TRIM(department)
        FROM employees
        WHERE department IS NOT NULL
          AND TRIM(department) <> ''
        ON CONFLICT (name) DO NOTHING
    """))

    # =========================================================
    # 5. Copy old designations
    # =========================================================

    connection.execute(sa.text("""
        INSERT INTO designations (name)
        SELECT DISTINCT TRIM(designation)
        FROM employees
        WHERE designation IS NOT NULL
          AND TRIM(designation) <> ''
        ON CONFLICT (name) DO NOTHING
    """))

    # =========================================================
    # 6. Convert department text → department_id
    # =========================================================

    connection.execute(sa.text("""
        UPDATE employees e
        SET department_id = d.id
        FROM departments d
        WHERE TRIM(e.department) = d.name
          AND e.department_id IS NULL
    """))

    # =========================================================
    # 7. Convert designation text → designation_id
    # =========================================================

    connection.execute(sa.text("""
        UPDATE employees e
        SET designation_id = d.id
        FROM designations d
        WHERE TRIM(e.designation) = d.name
          AND e.designation_id IS NULL
    """))

    # =========================================================
    # 8. Verify department conversion
    # =========================================================

    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM employees
        WHERE department_id IS NULL
    """))

    missing_departments = result.scalar()

    if missing_departments > 0:
        raise Exception(
            f"{missing_departments} employee(s) have no department assigned."
        )

    # =========================================================
    # 9. Verify designation conversion
    # =========================================================

    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM employees
        WHERE designation_id IS NULL
    """))

    missing_designations = result.scalar()

    if missing_designations > 0:
        raise Exception(
            f"{missing_designations} employee(s) have no designation assigned."
        )

    # =========================================================
    # 10. Add foreign keys if they don't already exist
    # =========================================================

    result = connection.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'employees'
          AND constraint_name = 'fk_employees_department'
    """))

    if result.fetchone() is None:

        connection.execute(sa.text("""
            ALTER TABLE employees
            ADD CONSTRAINT fk_employees_department
            FOREIGN KEY (department_id)
            REFERENCES departments(id)
        """))

    result = connection.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'employees'
          AND constraint_name = 'fk_employees_designation'
    """))

    if result.fetchone() is None:

        connection.execute(sa.text("""
            ALTER TABLE employees
            ADD CONSTRAINT fk_employees_designation
            FOREIGN KEY (designation_id)
            REFERENCES designations(id)
        """))

    # =========================================================
    # 11. Make columns NOT NULL
    # =========================================================

    connection.execute(sa.text("""
        ALTER TABLE employees
        ALTER COLUMN department_id SET NOT NULL
    """))

    connection.execute(sa.text("""
        ALTER TABLE employees
        ALTER COLUMN designation_id SET NOT NULL
    """))

    # =========================================================
    # 12. Remove old text columns
    # =========================================================

    connection.execute(sa.text("""
        ALTER TABLE employees
        DROP COLUMN IF EXISTS department
    """))

    connection.execute(sa.text("""
        ALTER TABLE employees
        DROP COLUMN IF EXISTS designation
    """))


def downgrade():

    connection = op.get_bind()

    # =========================================================
    # 1. Restore old text columns
    # =========================================================

    connection.execute(sa.text("""
        ALTER TABLE employees
        ADD COLUMN IF NOT EXISTS department VARCHAR(100)
    """))

    connection.execute(sa.text("""
        ALTER TABLE employees
        ADD COLUMN IF NOT EXISTS designation VARCHAR(100)
    """))

    # =========================================================
    # 2. Restore department names
    # =========================================================

    connection.execute(sa.text("""
        UPDATE employees e
        SET department = d.name
        FROM departments d
        WHERE e.department_id = d.id
    """))

    # =========================================================
    # 3. Restore designation names
    # =========================================================

    connection.execute(sa.text("""
        UPDATE employees e
        SET designation = d.name
        FROM designations d
        WHERE e.designation_id = d.id
    """))

    # =========================================================
    # 4. Remove foreign keys
    # =========================================================

    connection.execute(sa.text("""
        ALTER TABLE employees
        DROP CONSTRAINT IF EXISTS fk_employees_department
    """))

    connection.execute(sa.text("""
        ALTER TABLE employees
        DROP CONSTRAINT IF EXISTS fk_employees_designation
    """))

    # =========================================================
    # 5. Remove new columns
    # =========================================================

    connection.execute(sa.text("""
        ALTER TABLE employees
        DROP COLUMN IF EXISTS department_id
    """))

    connection.execute(sa.text("""
        ALTER TABLE employees
        DROP COLUMN IF EXISTS designation_id
    """))

    # =========================================================
    # 6. Drop tables
    # =========================================================

    connection.execute(sa.text("""
        DROP TABLE IF EXISTS designations
    """))

    connection.execute(sa.text("""
        DROP TABLE IF EXISTS departments
    """))