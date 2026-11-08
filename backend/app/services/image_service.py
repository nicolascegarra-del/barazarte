"""Validacion y procesado de imagenes subidas: MIME, EXIF fuera, WebP + miniatura."""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import AppError

# Limite anti "decompression bomb" (Pillow lanza DecompressionBombError por encima de 2x)
Image.MAX_IMAGE_PIXELS = 50_000_000

ALLOWED_MIME_TYPES = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
MAIN_MAX_SIDE = 2000
THUMB_MAX_SIDE = 480
WEBP_QUALITY = 85


@dataclass(frozen=True)
class ProcessedImage:
    main: bytes
    thumb: bytes
    width: int
    height: int


def _invalid(message: str) -> AppError:
    return AppError(422, "INVALID_IMAGE", message, field="file")


def _encode_webp(image: Image.Image, max_side: int) -> tuple[bytes, tuple[int, int]]:
    resized = image.copy()
    resized.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    # No se pasa exif= ni icc_profile=: el WebP resultante no lleva metadatos
    resized.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=4)
    return buffer.getvalue(), resized.size


def process_image(data: bytes, declared_mime: str | None, max_bytes: int) -> ProcessedImage:
    if declared_mime not in ALLOWED_MIME_TYPES:
        raise AppError(
            415,
            "UNSUPPORTED_MEDIA_TYPE",
            "Formato no admitido. Usa JPEG, PNG o WebP.",
            field="file",
        )
    if not data:
        raise _invalid("El archivo esta vacio.")
    if len(data) > max_bytes:
        raise AppError(
            413,
            "PAYLOAD_TOO_LARGE",
            f"La imagen supera el maximo de {max_bytes // (1024 * 1024)} MB.",
            field="file",
        )

    try:
        with Image.open(BytesIO(data)) as probe:
            # Se confia en el contenido real, no en la cabecera Content-Type
            if probe.format != ALLOWED_MIME_TYPES[declared_mime]:
                raise _invalid("El contenido del archivo no coincide con su tipo.")
            probe.verify()
        with Image.open(BytesIO(data)) as source:
            source.load()
            oriented = ImageOps.exif_transpose(source)
            mode = (
                "RGBA" if "A" in oriented.getbands() or "transparency" in oriented.info else "RGB"
            )
            converted = oriented.convert(mode)
            # Imagen nueva a partir de los pixeles: descarta EXIF, GPS, perfiles ICC y comentarios
            clean = Image.frombytes(mode, converted.size, converted.tobytes())
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as exc:
        raise _invalid(
            "No se pudo leer la imagen; el archivo esta corrupto o no es valido."
        ) from exc

    main_bytes, main_size = _encode_webp(clean, MAIN_MAX_SIDE)
    thumb_bytes, _ = _encode_webp(clean, THUMB_MAX_SIDE)
    return ProcessedImage(
        main=main_bytes, thumb=thumb_bytes, width=main_size[0], height=main_size[1]
    )
