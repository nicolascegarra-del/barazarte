"""Esquema inicial: artists, artworks, artwork_images, inquiries.

Revision ID: 0001
Revises:
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "artists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index("ix_artists_email", "artists", ["email"], unique=True)

    op.create_table(
        "artworks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artist_id",
            sa.Integer(),
            sa.ForeignKey("artists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("technique", sa.String(120), nullable=False),
        sa.Column("width_cm", sa.Numeric(7, 2), nullable=False),
        sa.Column("height_cm", sa.Numeric(7, 2), nullable=False),
        sa.Column("depth_cm", sa.Numeric(7, 2), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_artworks_artist_id", "artworks", ["artist_id"])
    op.create_index("ix_artworks_status_created", "artworks", ["status", "created_at"])

    op.create_table(
        "artwork_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artwork_id",
            sa.Integer(),
            sa.ForeignKey("artworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("thumb_key", sa.String(255), nullable=False),
        sa.Column("alt_text", sa.String(200), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_artwork_images_artwork_id", "artwork_images", ["artwork_id"])

    op.create_table(
        "inquiries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artist_id",
            sa.Integer(),
            sa.ForeignKey("artists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "artwork_id",
            sa.Integer(),
            sa.ForeignKey("artworks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("artwork_title", sa.String(200), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_inquiries_artist_status", "inquiries", ["artist_id", "status"])
    op.create_index("ix_inquiries_artwork_id", "inquiries", ["artwork_id"])


def downgrade() -> None:
    op.drop_table("inquiries")
    op.drop_table("artwork_images")
    op.drop_table("artworks")
    op.drop_table("artists")
