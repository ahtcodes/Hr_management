"""add paid unpaid payroll controls

Revision ID: 4839441e19e1
Revises: a912b3e53229
Create Date: 2026-08-11 12:16:08.782292

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision = '4839441e19e1'
down_revision = 'a912b3e53229'
branch_labels = None
depends_on = None


def upgrade():

    # ==================================================
    # Attendance
    # ==================================================

    with op.batch_alter_table(
        'attendance',
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                'late_paid',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true')
            )
        )

        batch_op.add_column(
            sa.Column(
                'early_leave_paid',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true')
            )
        )

    # ==================================================
    # Leave
    # ==================================================

    with op.batch_alter_table(
        'leaves',
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                'is_paid',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true')
            )
        )


def downgrade():

    # ==================================================
    # Leave
    # ==================================================

    with op.batch_alter_table(
        'leaves',
        schema=None
    ) as batch_op:

        batch_op.drop_column('is_paid')

    # ==================================================
    # Attendance
    # ==================================================

    with op.batch_alter_table(
        'attendance',
        schema=None
    ) as batch_op:

        batch_op.drop_column(
            'early_leave_paid'
        )

        batch_op.drop_column(
            'late_paid'
        )