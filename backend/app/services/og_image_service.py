"""Imagen para compartir (Open Graph): JPEG 1200x630 con la obra sobre fondo marfil."""

import logging
from io import BytesIO

from PIL import Image, ImageFilter

from app.core.storage import ObjectStorage

logger = logging.getLogger(__name__)

OG_WIDTH, OG_HEIGHT = 1200, 630
OG_MARGIN = 56
OG_BACKGROUND = (0xFA, 0xF8, 0xF4)
SHADOW_OFFSET = 10
SHADOW_BLUR = 18
SHADOW_ALPHA = 70
JPEG_QUALITIES = (85, 78, 70)
TARGET_MAX_BYTES = 300 * 1024


def og_cache_key(artwork_id: int, image_id: int) -> str:
    """Clave de cache: incluye el id de imagen, asi cambia al cambiar la principal."""
    return f"og/{artwork_id}-{image_id}.jpg"


def _encode_jpeg(canvas: Image.Image) -> bytes:
    """Codifica en JPEG bajando la calidad solo si supera el tamano objetivo."""
    data = b""
    for quality in JPEG_QUALITIES:
        buffer = BytesIO()
        canvas.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
        data = buffer.getvalue()
        if len(data) <= TARGET_MAX_BYTES:
            break
    return data


def render_og_image(source: bytes) -> bytes:
    """Compone la obra entera (sin recortar) centrada sobre fondo marfil con sombra suave.

    Se reduce la obra al area util antes de componer, para gastar poca memoria y CPU.

    Raises:
        OSError: si el origen no es una imagen legible.
    """
    box = (OG_WIDTH - 2 * OG_MARGIN, OG_HEIGHT - 2 * OG_MARGIN)
    with Image.open(BytesIO(source)) as opened:
        opened.draft("RGB", box)  # acelera la decodificacion de JPEG; no-op en otros formatos
        artwork = opened.convert("RGBA")
    artwork.thumbnail(box, Image.Resampling.LANCZOS)
    left = (OG_WIDTH - artwork.width) // 2
    top = (OG_HEIGHT - artwork.height) // 2

    canvas = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT), (*OG_BACKGROUND, 255))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow.paste(
        (0, 0, 0, SHADOW_ALPHA),
        (left, top + SHADOW_OFFSET, left + artwork.width, top + SHADOW_OFFSET + artwork.height),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(artwork, (left, top))
    return _encode_jpeg(canvas.convert("RGB"))


def get_or_create_og_image(
    storage: ObjectStorage, artwork_id: int, image_id: int, source_key: str
) -> bytes | None:
    """Devuelve el JPEG cacheado o lo genera y cachea.

    Devuelve None si el objeto de origen falta o no se puede leer.
    """
    key = og_cache_key(artwork_id, image_id)
    cached = storage.get(key)
    if cached is not None:
        return cached
    source = storage.get(source_key)
    if source is None:
        return None
    try:
        rendered = render_og_image(source)
    except (OSError, SyntaxError, Image.DecompressionBombError):
        logger.warning("Imagen de origen ilegible para og.jpg de la obra %s", artwork_id)
        return None
    try:
        storage.put(key, rendered, "image/jpeg")
    except Exception:
        # La cache es una optimizacion: si falla se sirve igualmente la imagen generada
        logger.exception("No se pudo cachear %s", key)
    return rendered
