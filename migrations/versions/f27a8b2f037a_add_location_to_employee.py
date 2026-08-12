"""add location to employee

Revision ID: f27a8b2f037a
Revises: c369c52a115d
Create Date: 2026-08-06 18:43:54.028564

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f27a8b2f037a'
down_revision = 'c369c52a115d'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('employees', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'employment_type',
                sa.String(length=20),
                nullable=False,
                server_default='Full Time'
            )
        )

        batch_op.add_column(
            sa.Column(
                'location',
                sa.String(length=100),
                nullable=False,
                server_default='Faisalabad'
            )
        )


def downgrade():
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.drop_column('location')
        batch_op.drop_column('employment_type')