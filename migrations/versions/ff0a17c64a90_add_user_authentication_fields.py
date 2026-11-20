
"""Add user authentication fields

Revision ID: ff0a17c64a90
Revises: 6b4b4510a8e6
"""

from alembic import op
import sqlalchemy as sa


revision = "ff0a17c64a90"
down_revision = "6b4b4510a8e6"
branch_labels = None
depends_on = None


def upgrade():
    # Додаємо поле для хешу пароля
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )

    # Додаємо роль із тимчасовим дозволом NULL
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=True),
    )

    # Призначаємо існуючим користувачам роль user
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")

    # Робимо поле ролі обов'язковим
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=20),
        nullable=False,
    )


def downgrade():
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
