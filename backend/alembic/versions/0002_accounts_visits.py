"""Cuentas (verificacion, admin, limite de obras) y visitas agregadas.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_MAX_ARTWORKS = 5


def upgrade() -> None:
    op.add_column(
        "artists",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Los artistas existentes (creados por CLI) quedan verificados
    op.add_column(
        "artists",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "artists",
        sa.Column(
            "max_artworks", sa.Integer(), nullable=True, server_default=str(DEFAULT_MAX_ARTWORKS)
        ),
    )
    # Los nuevos registros fijan el valor desde la aplicacion (false hasta verificar)
    op.alter_column("artists", "email_verified", server_default=None)
    op.alter_column("artists", "max_artworks", server_default=None)

    op.create_table(
        "visits_daily",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("artwork_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("date", "artwork_id"),
    )


def downgrade() -> None:
    op.drop_table("visits_daily")
    op.drop_column("artists", "max_artworks")
    op.drop_column("artists", "email_verified")
    op.drop_column("artists", "is_admin")
