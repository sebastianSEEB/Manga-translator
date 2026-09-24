import base64
import binascii
from io import BytesIO
import warnings
from PIL import Image, UnidentifiedImageError
from backend.config import MAX_PIXELS

Image.MAX_IMAGE_PIXELS = MAX_PIXELS

def decode_png(value):
    if value.startswith("data:"):
        prefix = "data:image/png;base64,"
        if not value.startswith(prefix):
            raise ValueError("Use a PNG data URL or raw base64 PNG.")
        value = value[len(prefix):]
    try:
        raw = base64.b64decode(value, validate=True)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as img:
                if img.format != "PNG":
                    raise ValueError("Only PNG screenshots are accepted.")
                if img.width * img.height > MAX_PIXELS:
                    raise ValueError("Screenshot exceeds 20 million pixels.")
                img.load()
                # Composite transparency on white rather than introducing black pixels.
                rgba = img.convert("RGBA")
                background = Image.new("RGBA", rgba.size, "white")
                return Image.alpha_composite(background, rgba).convert("RGB")
    except (binascii.Error, UnidentifiedImageError, OSError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("Invalid, corrupt or oversized PNG screenshot.") from exc

def clamp_box(xyxy, width, height):
    x1, y1, x2, y2 = (int(v) for v in xyxy)
    x1, x2 = max(0, min(width, x1)), max(0, min(width, x2))
    y1, y2 = max(0, min(height, y1)), max(0, min(height, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2 - x1, y2 - y1)
