
"""Add category ownership

Revision ID: 50614194873d
Revises: ff0a17c64a90
"""

from alembic import op
import sqlalchemy as sa


revision = "50614194873d"
down_revision = "ff0a17c64a90"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("categories") as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_categories_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade():
    with op.batch_alter_table("categories") as batch_op:
        batch_op.drop_constraint(
            "fk_categories_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("user_id")
