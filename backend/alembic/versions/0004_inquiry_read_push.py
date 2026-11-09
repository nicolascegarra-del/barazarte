"""Consultas leidas/sin leer y suscripciones Web Push.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("inquiries", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    # Las consultas existentes se dan por leidas para no inundar el contador
    op.execute("UPDATE inquiries SET read_at = created_at")
    op.create_index("ix_inquiries_artist_read", "inquiries", ["artist_id", "read_at"])

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(length=256), nullable=False),
        sa.Column("auth", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint"),
    )
    op.create_index("ix_push_subscriptions_artist_id", "push_subscriptions", ["artist_id"])


def downgrade() -> None:
    op.drop_index("ix_push_subscriptions_artist_id", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
    op.drop_index("ix_inquiries_artist_read", table_name="inquiries")
    op.drop_column("inquiries", "read_at")
