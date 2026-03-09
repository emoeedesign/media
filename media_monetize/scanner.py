"""
Media Scanner - ローカルの写真・動画を検索・分類するモジュール
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Iterator

try:
    from PIL import Image
    import piexif
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp", ".heic", ".raw", ".cr2", ".nef", ".arw"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".mts", ".m2ts"}

STOCK_MIN_PHOTO_PIXELS = 4_000_000   # 4MP 以上を「販売可能」とみなす
STOCK_MIN_VIDEO_SECONDS = 5          # 5秒以上


def _file_hash(path: Path, chunk: int = 65536) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _photo_meta(path: Path) -> dict:
    meta = {"width": None, "height": None, "megapixels": None,
            "exif_date": None, "camera": None, "sellable": False}
    if not PIL_AVAILABLE:
        return meta
    try:
        with Image.open(path) as img:
            meta["width"], meta["height"] = img.size
            mp = img.size[0] * img.size[1]
            meta["megapixels"] = round(mp / 1_000_000, 2)
            meta["sellable"] = mp >= STOCK_MIN_PHOTO_PIXELS
            # EXIF
            if "exif" in img.info:
                exif = piexif.load(img.info["exif"])
                dt = exif.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal, b"")
                if dt:
                    meta["exif_date"] = dt.decode("ascii", errors="ignore")
                make = exif.get("0th", {}).get(piexif.ImageIFD.Make, b"")
                model = exif.get("0th", {}).get(piexif.ImageIFD.Model, b"")
                if make or model:
                    meta["camera"] = f"{make.decode('ascii', errors='ignore').strip()} {model.decode('ascii', errors='ignore').strip()}".strip()
    except Exception:
        pass
    return meta


def _video_meta(path: Path) -> dict:
    meta = {"duration_sec": None, "width": None, "height": None, "fps": None, "sellable": False}
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if cap.isOpened():
            meta["fps"] = cap.get(cv2.CAP_PROP_FPS)
            meta["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            meta["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if meta["fps"] and meta["fps"] > 0:
                meta["duration_sec"] = round(frames / meta["fps"], 2)
                meta["sellable"] = meta["duration_sec"] >= STOCK_MIN_VIDEO_SECONDS
        cap.release()
    except Exception:
        pass
    return meta


def scan_directory(root: str | Path, recursive: bool = True) -> Iterator[dict]:
    """
    ディレクトリ内の写真・動画を全てスキャンし、メタ情報を yield する。

    Yields:
        dict: {path, type, size_bytes, modified, md5, ...media_meta}
    """
    root = Path(root)
    pattern = "**/*" if recursive else "*"
    for p in root.glob(pattern):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in PHOTO_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
            continue

        media_type = "photo" if ext in PHOTO_EXTENSIONS else "video"
        stat = p.stat()
        record = {
            "path": str(p),
            "filename": p.name,
            "type": media_type,
            "extension": ext,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / 1_048_576, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "md5": _file_hash(p),
        }

        if media_type == "photo":
            record.update(_photo_meta(p))
        else:
            record.update(_video_meta(p))

        yield record


def scan_to_json(root: str | Path, output: str | Path, recursive: bool = True) -> list[dict]:
    """スキャン結果を JSON ファイルに保存して返す。"""
    results = list(scan_directory(root, recursive))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


def deduplicate(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """MD5 が同じファイルを重複として分離する。"""
    seen: dict[str, dict] = {}
    dupes: list[dict] = []
    unique: list[dict] = []
    for r in records:
        h = r["md5"]
        if h in seen:
            dupes.append(r)
        else:
            seen[h] = r
            unique.append(r)
    return unique, dupes
