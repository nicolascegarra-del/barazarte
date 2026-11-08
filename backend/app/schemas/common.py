import math
from dataclasses import dataclass
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

MAX_PAGE_SIZE = 50


@dataclass
class PaginationParams:
    page: Annotated[int, Query(ge=1, description="Pagina (base 1)")] = 1
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Elementos por pagina")] = (
        20
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=math.ceil(total / params.page_size) if total else 0,
        )
