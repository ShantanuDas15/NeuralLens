"""Image Processing Utilities.

Provides preprocessing and postprocessing functions for image enhancement:
- Validating file sizes.
- Decoding raw bytes to OpenCV BGR numpy arrays.
- Encoding OpenCV BGR numpy arrays to PNG bytes.
"""

from __future__ import annotations

from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG"}


def inspect_image(raw_bytes: bytes) -> tuple[str, int, int]:
    """Read only the image header: return (format, width, height).

    Does not decode pixel data, so it is cheap and safe to call before the
    pixel-count limits are enforced.

    Raises:
        ValueError: If the bytes are not a readable JPEG or PNG.
    """
    try:
        with Image.open(BytesIO(raw_bytes)) as img:
            fmt, (width, height) = img.format, img.size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("Invalid, corrupt, or unsupported image format.") from exc

    if fmt not in ALLOWED_FORMATS:
        raise ValueError("Unsupported file format. Only JPEG and PNG are allowed.")
    return fmt, width, height


def validate_and_decode(raw_bytes: bytes, max_bytes: int) -> np.ndarray:
    """Validate image size and decode to an OpenCV BGR numpy array.

    Args:
        raw_bytes: The raw image file bytes (e.g. uploaded via multipart).
        max_bytes: The maximum allowed size in bytes.

    Returns:
        np.ndarray: The decoded image in BGR format with shape (H, W, 3).

    Raises:
        ValueError: If the file is too large, corrupt, or an unsupported format.
    """
    size = len(raw_bytes)
    if size > max_bytes:
        raise ValueError(
            f"Image size exceeds the maximum allowed limit "
            f"({size} > {max_bytes} bytes)."
        )

    # Convert bytes to numpy array
    nparr = np.frombuffer(raw_bytes, np.uint8)

    # Decode image using OpenCV
    # cv2.IMREAD_COLOR ensures it's always read as BGR, ignoring alpha channels
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise ValueError("Invalid, corrupt, or unsupported image format.")

    return img_bgr


def encode_to_png(bgr_array: np.ndarray) -> bytes:
    """Encode an OpenCV BGR numpy array into PNG bytes.

    Args:
        bgr_array: The image array in BGR format.

    Returns:
        bytes: The encoded PNG file bytes.

    Raises:
        ValueError: If encoding fails.
    """
    success, encoded_img = cv2.imencode(".png", bgr_array)
    if not success:
        raise ValueError("Failed to encode image to PNG format.")

    return encoded_img.tobytes()
