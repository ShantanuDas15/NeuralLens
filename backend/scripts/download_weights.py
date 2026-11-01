"""Download Real-ESRGAN weights into ./weights, verifying size and SHA-256.

Run at Docker build time so the image is self-contained (the .pth files are
gitignored and are not in the repository). Idempotent: files that already
exist with the right checksum are skipped.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"
BASE = "https://github.com/xinntao/Real-ESRGAN/releases/download"

# name -> (url, size_bytes, sha256). Sizes match the official release assets.
WEIGHTS = {
    "RealESRGAN_x4plus.pth": (
        f"{BASE}/v0.1.0/RealESRGAN_x4plus.pth",
        67040989,
        "4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1",
    ),
    "RealESRGAN_x2plus.pth": (
        f"{BASE}/v0.2.1/RealESRGAN_x2plus.pth",
        67061725,
        "49fafd45f8fd7aa8d31ab2a22d14d91b536c34494a5cfe31eb5d89c2fa266ab",
    ),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    for name, (url, size, sha) in WEIGHTS.items():
        dest = WEIGHTS_DIR / name
        if dest.exists() and dest.stat().st_size == size and _sha256(dest) == sha:
            print(f"ok (cached): {name}")
            continue
        print(f"downloading {name} ...")
        tmp = dest.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)  # noqa: S310 - fixed https URL
        if tmp.stat().st_size != size or _sha256(tmp) != sha:
            tmp.unlink(missing_ok=True)
            print(f"ERROR: checksum mismatch for {name}", file=sys.stderr)
            return 1
        tmp.replace(dest)
        print(f"ok: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
