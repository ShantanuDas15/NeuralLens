"""SRGAN Inference Service.

Manages the Real-ESRGAN model lifecycle and executes image enhancement.
- Singleton model instance loaded at application startup.
- Uses CUDA if available, falls back to CPU.
- Orchestrates image preprocessing, inference, and postprocessing.
"""

from __future__ import annotations

import logging
import os

# Patch for basicsr compatibility with newer torchvision versions
import sys
import time
from typing import Any

import torch
import torchvision

sys.modules["torchvision.transforms.functional_tensor"] = (
    torchvision.transforms.functional
)

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

from config import settings
from services.image_utils import encode_to_png, validate_and_decode

logger = logging.getLogger(__name__)

# Module-level dictionary to hold the loaded models
_model_instances: dict[int, RealESRGANer] = {}

# Hardcoded model path relative to this file's directory
_WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "weights")


def load_model() -> None:
    """Initialize and load the RealESRGANer models into memory."""
    global _model_instances

    if _model_instances:
        logger.info("SRGAN models are already loaded.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Define models to load
    configs = [
        {"scale": 4, "filename": "RealESRGAN_x4plus.pth", "model_scale": 4, "num_block": 23},
        {"scale": 2, "filename": "RealESRGAN_x2plus.pth", "model_scale": 2, "num_block": 23},
    ]

    for cfg in configs:
        weights_path = os.path.join(_WEIGHTS_DIR, cfg["filename"])
        if not os.path.exists(weights_path):
            logger.warning(f"Model weights not found at {weights_path}, skipping {cfg['scale']}x")
            continue

        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=cfg["num_block"],
            num_grow_ch=32,
            scale=cfg["model_scale"],
        )

        _model_instances[cfg["scale"]] = RealESRGANer(
            scale=cfg["model_scale"],
            model_path=weights_path,
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=device == "cuda",
            device=torch.device(device),
        )
        logger.info(f"SRGAN {cfg['scale']}x model loaded on {device}")

    # Aliases
    if 4 in _model_instances:
        _model_instances[8] = _model_instances[4] # x8 uses x4 network but outscale=8


def enhance_image(input_bytes: bytes, scale: int = 4) -> tuple[bytes, dict[str, Any]]:
    """Process an image byte payload through the SRGAN model.

    Args:
        input_bytes: The raw image file bytes.
        scale: The requested upscale factor.

    Returns:
        tuple[bytes, dict]: A tuple containing:
            - The upscaled image bytes (encoded as PNG).
            - A metadata dictionary with processing metrics.

    Raises:
        RuntimeError: If the model has not been loaded via load_model().
        ValueError: If the input bytes are invalid, corrupt, or too large.
    """
    if not _model_instances:
        raise RuntimeError("SRGAN models are not loaded. Call load_model() first.")
        
    model_instance = _model_instances.get(scale)
    if model_instance is None:
        raise ValueError(f"SRGAN model for scale {scale}x is not available.")

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
        out_bgr, _ = model_instance.enhance(img_bgr, outscale=scale)
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
