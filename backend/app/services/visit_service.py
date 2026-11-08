"""Visitas agregadas por dia: sin cookies, sin IP, sin user-agent."""

from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session

from app.models import PUBLIC_ARTWORK_STATUSES, Artist, Artwork, VisitDaily
from app.models.visit import GENERAL_VISIT_ARTWORK_ID


def today_utc() -> date:
    return datetime.now(UTC).date()


def _is_trackable(session: Session, artwork_id: int) -> bool:
    artwork = session.get(Artwork, artwork_id)
    if artwork is None or artwork.status not in PUBLIC_ARTWORK_STATUSES:
        return False
    owner = session.get(Artist, artwork.artist_id)
    return owner is not None and owner.is_active


def record_visit(session: Session, artwork_id: int | None) -> None:
    """Suma 1 al contador (dia, obra) con un upsert atomico. Si la obra no existe o no es
    publica se ignora en silencio (no se revela que obras existen)."""
    if artwork_id is not None and not _is_trackable(session, artwork_id):
        return
    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    statement = insert(VisitDaily).values(  # type: ignore[arg-type]
        date=today_utc(),
        artwork_id=artwork_id if artwork_id is not None else GENERAL_VISIT_ARTWORK_ID,
        count=1,
    )
    statement = statement.on_conflict_do_update(
        index_elements=["date", "artwork_id"],
        set_={"count": VisitDaily.__table__.c.count + 1},  # type: ignore[attr-defined]
    )
    session.exec(statement)  # type: ignore[call-overload]
    session.commit()
