from enum import StrEnum


class ArtworkStatus(StrEnum):
    DRAFT = "borrador"
    PUBLISHED = "publicado"
    RESERVED = "reservado"
    SOLD = "vendido"


# Estados visibles en la galeria publica (el borrador nunca se expone)
PUBLIC_ARTWORK_STATUSES = (ArtworkStatus.PUBLISHED, ArtworkStatus.RESERVED, ArtworkStatus.SOLD)


class InquiryStatus(StrEnum):
    NEW = "nueva"
    CONTACTED = "contactado"
    SOLD = "vendida"
