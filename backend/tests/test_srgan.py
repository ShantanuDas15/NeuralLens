"""Milestone 1.4 — SRGAN Inference Service Tests.

Tests the image enhancement pipeline using mock inference to avoid GPU requirements.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services import srgan
from services.image_utils import validate_and_decode

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure the singleton is reset before each test."""
    srgan._model_instance = None
    yield
    srgan._model_instance = None


@pytest.fixture
def mock_weights_path():
    """Mock the weights path check."""
    with patch("os.path.exists", return_value=True):
        yield


@pytest.fixture
def mock_realesrganer():
    """Mock the RealESRGANer instance and its enhance() method."""
    mock_instance = MagicMock()

    def fake_enhance(img_bgr, outscale=4):
        # Return a dummy upscaled numpy array (H*4, W*4, 3)
        h, w = img_bgr.shape[:2]
        out_bgr = np.zeros((h * outscale, w * outscale, 3), dtype=np.uint8)
        return out_bgr, None

    mock_instance.enhance.side_effect = fake_enhance

    with patch("services.srgan.RealESRGANer", return_value=mock_instance):
        yield mock_instance


@pytest.fixture
def sample_png_bytes():
    """Return raw bytes of a valid 64x64 PNG."""
    path = Path("tests/fixtures/sample_lr.png")
    if not path.exists():
        pytest.skip("Fixture sample_lr.png not found")
    return path.read_bytes()


@pytest.fixture
def sample_jpg_bytes():
    """Return raw bytes of a valid 64x64 JPEG."""
    path = Path("tests/fixtures/sample_lr.jpg")
    if not path.exists():
        pytest.skip("Fixture sample_lr.jpg not found")
    return path.read_bytes()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_load_model_success(mock_weights_path, mock_realesrganer):
    """Test 1: load_model() succeeds and sets the singleton."""
    assert srgan._model_instance is None
    srgan.load_model()
    assert srgan._model_instance is not None


def test_enhance_image_raises_if_not_loaded(sample_png_bytes):
    """Test 2: enhance_image() called before load_model() raises RuntimeError."""
    with pytest.raises(RuntimeError, match="not loaded"):
        srgan.enhance_image(sample_png_bytes)


def test_enhance_image_valid_png(
    mock_weights_path, mock_realesrganer, sample_png_bytes
):
    """Test 3: enhance_image() with valid 64x64 PNG bytes → returns bytes + metadata dict."""
    srgan.load_model()
    result_bytes, metadata = srgan.enhance_image(sample_png_bytes)

    assert isinstance(result_bytes, bytes)
    assert len(result_bytes) > 0
    assert isinstance(metadata, dict)


def test_enhance_image_metadata_keys(
    mock_weights_path, mock_realesrganer, sample_png_bytes
):
    """Test 4: metadata dict contains correct keys."""
    srgan.load_model()
    _, metadata = srgan.enhance_image(sample_png_bytes)

    expected_keys = {
        "input_width",
        "input_height",
        "output_width",
        "output_height",
        "processing_time_ms",
    }
    assert expected_keys.issubset(metadata.keys())


def test_enhance_image_output_dimensions(
    mock_weights_path, mock_realesrganer, sample_png_bytes
):
    """Test 5: output_width = input_width * 4, output_height = input_height * 4."""
    srgan.load_model()
    _, metadata = srgan.enhance_image(sample_png_bytes)

    assert metadata["output_width"] == metadata["input_width"] * 4
    assert metadata["output_height"] == metadata["input_height"] * 4


def test_validate_and_decode_oversized_bytes(sample_png_bytes):
    """Test 6: validate_and_decode() with oversized bytes raises ValueError."""
    # max_bytes = 10 -> will fail
    with pytest.raises(ValueError, match="exceeds the maximum allowed limit"):
        validate_and_decode(sample_png_bytes, max_bytes=10)


def test_validate_and_decode_corrupt_bytes():
    """Test 7: validate_and_decode() with corrupt non-image bytes raises ValueError."""
    corrupt_bytes = b"This is just random text, not an image."
    with pytest.raises(ValueError, match="Invalid, corrupt, or unsupported"):
        validate_and_decode(corrupt_bytes, max_bytes=1000)


def test_validate_and_decode_valid_jpeg(sample_jpg_bytes):
    """Test 8: validate_and_decode() with valid JPEG bytes → returns numpy array of correct shape."""
    img_bgr = validate_and_decode(sample_jpg_bytes, max_bytes=1024 * 1024)

    assert isinstance(img_bgr, np.ndarray)
    assert img_bgr.shape == (64, 64, 3)
