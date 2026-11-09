"""Schemas del catalogo publico: facetas y obras vecinas."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

ArtworkSize = Literal["pequeno", "mediano", "grande"]
ArtworkSort = Literal["recientes", "precio_asc", "precio_desc"]


class TechniqueFacet(BaseModel):
    name: str
    count: int


class ArtistFacet(BaseModel):
    id: int
    display_name: str
    count: int


class PriceRange(BaseModel):
    min: Decimal | None
    max: Decimal | None


class ArtworkFacets(BaseModel):
    techniques: list[TechniqueFacet]
    artists: list[ArtistFacet]
    price: PriceRange
    total: int


class ArtworkRef(BaseModel):
    id: int
    title: str


class ArtworkNeighbors(BaseModel):
    prev: ArtworkRef | None
    next: ArtworkRef | None
