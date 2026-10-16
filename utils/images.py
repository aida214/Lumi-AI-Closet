"""Prepare uploaded photos: fix rotation, flatten transparency, shrink, compress."""
import io

from PIL import Image, ImageOps, UnidentifiedImageError

from utils.constants import MAX_UPLOAD_MB

MAX_SIDE = 1200


class ImageError(ValueError):
    """Raised with a message that is safe to show to the user."""


def prepare_upload(data):
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ImageError(f"That photo is larger than {MAX_UPLOAD_MB} MB. Please choose a smaller one.")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise ImageError("That file could not be read as an image. Try a JPG, PNG or WebP photo.")
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    else:
        img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=86, optimize=True)
    return out.getvalue()
