from datetime import date as Date

from sqlmodel import Field, SQLModel

# artwork_id usado para las visitas que no son de una obra concreta (portada, listados...)
GENERAL_VISIT_ARTWORK_ID = 0


class VisitDaily(SQLModel, table=True):
    """Contador agregado de visitas por dia y obra. No guarda IP, user-agent ni cookies.

    Sin FK a artworks: asi el historico sobrevive al borrado de una obra y la clave
    compuesta (date, artwork_id) es unica tambien para las visitas generales (id 0),
    lo que permite un upsert atomico en cualquier base de datos."""

    __tablename__ = "visits_daily"

    date: Date = Field(primary_key=True)
    artwork_id: int = Field(default=GENERAL_VISIT_ARTWORK_ID, primary_key=True)
    count: int = Field(default=0)
