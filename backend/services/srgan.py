"""SRGAN Inference Service.

Manages the Real-ESRGAN model lifecycle and executes image enhancement.
- Singleton model instance loaded at application startup.
- Uses CUDA if available, falls back to CPU.
- Orchestrates image preprocessing, inference, and postprocessing.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

from config import settings
from services.image_utils import encode_to_png, validate_and_decode

logger = logging.getLogger(__name__)

# Module-level singleton to hold the loaded model
_model_instance: RealESRGANer | None = None

# Hardcoded model path relative to this file's directory since it's inside backend/services/
_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "weights", "RealESRGAN_x4plus.pth"
)


def load_model() -> None:
    """Initialize and load the RealESRGANer model into memory.

    Called once during the FastAPI application lifespan startup.
    Selects CUDA device if available, otherwise falls back to CPU.
    """
    global _model_instance

    if _model_instance is not None:
        logger.info("SRGAN model is already loaded.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if not os.path.exists(_WEIGHTS_PATH):
        raise FileNotFoundError(f"Model weights not found at {_WEIGHTS_PATH}")

    # Initialize the underlying RRDBNet architecture (RealESRGAN_x4plus specific)
    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=4,
    )

    # Initialize the RealESRGANer wrapper
    _model_instance = RealESRGANer(
        scale=4,
        model_path=_WEIGHTS_PATH,
        model=model,
        tile=0,  # 0 means no tiling, process whole image at once
        tile_pad=10,
        pre_pad=0,
        half=device == "cuda",  # use fp16 on GPU to save memory and speed up
        device=torch.device(device),
    )

    logger.info("SRGAN model loaded on %s", device)


def enhance_image(input_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    """Process an image byte payload through the SRGAN model.

    Args:
        input_bytes: The raw image file bytes.

    Returns:
        tuple[bytes, dict]: A tuple containing:
            - The upscaled image bytes (encoded as PNG).
            - A metadata dictionary with processing metrics.

    Raises:
        RuntimeError: If the model has not been loaded via load_model().
        ValueError: If the input bytes are invalid, corrupt, or too large.
    """
    if _model_instance is None:
        raise RuntimeError("SRGAN model is not loaded. Call load_model() first.")

    start_time = time.perf_counter()

    # 1. Preprocess: validate size and decode to BGR numpy array
    try:
        img_bgr = validate_and_decode(input_bytes, settings.max_upload_bytes)
    except Exception as exc:
        # Re-raise with consistent type for the router to catch
        raise ValueError(str(exc)) from exc

    input_height, input_width = img_bgr.shape[:2]

    # 2. Inference: Run the super-resolution model
    # out_bgr is the upscaled BGR numpy array
    try:
        out_bgr, _ = _model_instance.enhance(img_bgr, outscale=4)
    except Exception as exc:
        logger.error("Inference failed: %s", exc, exc_info=True)
        raise RuntimeError("Model inference failed.") from exc

    output_height, output_width = out_bgr.shape[:2]

    # 3. Postprocess: encode back to PNG bytes
    try:
        result_bytes = encode_to_png(out_bgr)
    except Exception as exc:
        raise ValueError("Failed to encode upscaled image.") from exc

    end_time = time.perf_counter()
    processing_time_ms = int((end_time - start_time) * 1000)

    metadata = {
        "input_width": input_width,
        "input_height": input_height,
        "output_width": output_width,
        "output_height": output_height,
        "processing_time_ms": processing_time_ms,
    }

    return result_bytes, metadata
