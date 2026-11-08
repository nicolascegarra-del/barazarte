from io import BytesIO

import pytest
from PIL import Image

from app.core.errors import AppError
from app.services.image_service import MAIN_MAX_SIDE, THUMB_MAX_SIDE, process_image

MAX_BYTES = 10 * 1024 * 1024


def _jpeg_with_exif(size: tuple[int, int]) -> bytes:
    exif = Image.Exif()
    exif[0x010F] = "CamaraSecreta"  # Make
    exif[0x8825] = {1: "N", 2: (40.0, 25.0, 0.0)}  # GPS IFD
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def test_process_image_cuando_jpeg_con_exif_entonces_webp_sin_metadatos() -> None:
    source = _jpeg_with_exif((3000, 1500))
    assert Image.open(BytesIO(source)).getexif()  # precondicion: el original lleva EXIF

    result = process_image(source, "image/jpeg", MAX_BYTES)

    main = Image.open(BytesIO(result.main))
    assert main.format == "WEBP"
    assert not main.getexif()
    assert b"CamaraSecreta" not in result.main
    assert max(main.size) == MAIN_MAX_SIDE
    assert (result.width, result.height) == main.size


def test_process_image_cuando_imagen_grande_entonces_miniatura_respeta_limite() -> None:
    result = process_image(_jpeg_with_exif((1200, 800)), "image/jpeg", MAX_BYTES)

    thumb = Image.open(BytesIO(result.thumb))
    assert thumb.format == "WEBP"
    assert max(thumb.size) == THUMB_MAX_SIDE


def test_process_image_cuando_mime_declarado_no_coincide_con_contenido_entonces_error() -> None:
    with pytest.raises(AppError) as error:
        process_image(_jpeg_with_exif((100, 100)), "image/png", MAX_BYTES)

    assert error.value.code == "INVALID_IMAGE"


def test_process_image_cuando_excede_el_tamano_maximo_entonces_413() -> None:
    with pytest.raises(AppError) as error:
        process_image(_jpeg_with_exif((100, 100)), "image/jpeg", 10)

    assert error.value.status_code == 413
