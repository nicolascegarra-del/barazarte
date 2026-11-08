"""Utilidades compartidas por los modelos."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum


def utcnow() -> datetime:
    return datetime.now(UTC)


def timestamp_column() -> Column:
    return Column(DateTime(timezone=True), nullable=False)


def enum_column(enum_class: type[StrEnum], *, index: bool = False) -> Column:
    """Enum guardado como VARCHAR con el *valor* (sin tipo nativo: migraciones mas simples)."""
    return Column(
        SAEnum(
            enum_class,
            native_enum=False,
            length=20,
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
        index=index,
    )
