"""Normalise uploaded photos before they are stored.

Phone photos arrive large (3-5 MB), often rely on an EXIF orientation flag
instead of rotated pixels, and carry EXIF metadata including GPS location.
For a children's home, publishing the location metadata of photos of
children is a safeguarding problem, so every new upload is:

* rotated according to its EXIF orientation,
* downscaled so the longest edge is at most ``max_edge`` pixels,
* re-encoded without any EXIF/GPS metadata.

Processing is best-effort: if Pillow cannot handle the file, the original
upload is kept unchanged.
"""

from __future__ import annotations

import logging
import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

DEFAULT_MAX_EDGE = 2000
JPEG_QUALITY = 85


def optimize_uploaded_image(instance, field_name: str, max_edge: int = DEFAULT_MAX_EDGE) -> None:
    """Replace a newly uploaded image on ``instance.<field_name>`` with a web-ready copy.

    Call this from ``Model.save()`` before ``super().save()``. Images that are
    already stored (i.e. not a fresh upload) are left alone.
    """
    field_file = getattr(instance, field_name, None)
    if not field_file or getattr(field_file, '_committed', True):
        return

    try:
        field_file.seek(0)
        with Image.open(field_file) as source:
            if getattr(source, 'is_animated', False):
                return  # keep animated GIF/WebP as-is

            image = ImageOps.exif_transpose(source)
            has_alpha = image.mode in ('RGBA', 'LA') or (
                image.mode == 'P' and 'transparency' in image.info
            )
            image = image.convert('RGBA' if has_alpha else 'RGB')
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)

            buffer = BytesIO()
            if has_alpha:
                image.save(buffer, format='PNG', optimize=True)
                extension = 'png'
            else:
                image.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
                extension = 'jpg'
    except Exception:  # noqa: BLE001 - never block an upload because optimisation failed
        logger.warning('Image optimisation skipped for %s.%s', type(instance).__name__, field_name, exc_info=True)
        try:
            field_file.seek(0)
        except Exception:  # noqa: BLE001
            pass
        return

    base_name = os.path.splitext(os.path.basename(field_file.name or 'image'))[0] or 'image'
    setattr(instance, field_name, ContentFile(buffer.getvalue(), name=f'{base_name}.{extension}'))
