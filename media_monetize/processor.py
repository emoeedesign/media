"""
Media Processor - ウォーターマーク付与・リサイズ・変換
販売用プレビューと納品ファイルを生成する
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---- 写真向けプリセット ----------------------------------------------------------------

PHOTO_PRESETS: dict[str, dict] = {
    "stock_full": {
        "description": "ストックサイト納品用 (長辺 6000px 以内, JPEG 品質 95)",
        "max_long_side": 6000,
        "format": "JPEG",
        "quality": 95,
    },
    "stock_preview": {
        "description": "プレビュー用 (長辺 1200px, ウォーターマーク付き)",
        "max_long_side": 1200,
        "format": "JPEG",
        "quality": 85,
        "watermark": True,
    },
    "web_medium": {
        "description": "Web 掲載用 (長辺 1920px)",
        "max_long_side": 1920,
        "format": "JPEG",
        "quality": 90,
    },
    "thumbnail": {
        "description": "サムネイル (320×320 正方形クロップ)",
        "square": 320,
        "format": "JPEG",
        "quality": 80,
    },
}


def _fit_size(w: int, h: int, max_long_side: int) -> tuple[int, int]:
    long = max(w, h)
    if long <= max_long_side:
        return w, h
    ratio = max_long_side / long
    return int(w * ratio), int(h * ratio)


def _add_watermark(img: "Image.Image", text: str = "© PREVIEW", opacity: int = 80) -> "Image.Image":
    """半透明テキストウォーターマークを対角線上に繰り返し配置する。"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(20, img.width // 20)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    step_x = tw + 60
    step_y = th + 60
    for y in range(-step_y, img.height + step_y, step_y):
        for x in range(-step_x, img.width + step_x, step_x):
            draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

    result = Image.alpha_composite(img.convert("RGBA"), overlay)
    return result.convert("RGB")


def process_photo(
    src: str | Path,
    dest_dir: str | Path,
    preset: str = "stock_preview",
    watermark_text: str = "© PREVIEW",
) -> Path:
    """
    写真を指定プリセットで処理して dest_dir に保存する。

    Returns:
        出力ファイルのパス
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow が必要です: pip install Pillow")

    src = Path(src)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    p = PHOTO_PRESETS.get(preset)
    if p is None:
        raise ValueError(f"未知のプリセット: {preset}. 選択肢: {list(PHOTO_PRESETS)}")

    with Image.open(src) as img:
        # EXIF 情報を保持しながら回転補正
        try:
            import piexif
            exif_bytes = img.info.get("exif", b"")
            exif_dict = piexif.load(exif_bytes) if exif_bytes else {}
            orientation = exif_dict.get("0th", {}).get(piexif.ImageIFD.Orientation, 1)
            rotation = {3: 180, 6: 270, 8: 90}.get(orientation)
            if rotation:
                img = img.rotate(rotation, expand=True)
        except Exception:
            exif_bytes = b""
            exif_dict = {}

        img = img.convert("RGB")

        if "square" in p:
            size = p["square"]
            img = img.resize((_fit_size(img.width, img.height, size * 4)[0],
                               _fit_size(img.width, img.height, size * 4)[1]), Image.LANCZOS)
            left = (img.width - size) // 2
            top = (img.height - size) // 2
            img = img.crop((left, top, left + size, top + size))
        elif "max_long_side" in p:
            new_w, new_h = _fit_size(img.width, img.height, p["max_long_side"])
            if (new_w, new_h) != (img.width, img.height):
                img = img.resize((new_w, new_h), Image.LANCZOS)

        if p.get("watermark"):
            img = _add_watermark(img, watermark_text)

        ext = ".jpg" if p["format"] == "JPEG" else f".{p['format'].lower()}"
        dest = dest_dir / f"{src.stem}_{preset}{ext}"

        save_kwargs: dict = {"quality": p.get("quality", 90), "optimize": True}
        img.save(dest, p["format"], **save_kwargs)

    return dest


def batch_process_photos(
    records: list[dict],
    output_root: str | Path,
    presets: list[str] | None = None,
    watermark_text: str = "© PREVIEW",
) -> list[dict]:
    """
    スキャン結果のリストを受け取り、指定プリセットで一括処理する。

    Returns:
        処理結果のサマリーリスト
    """
    if presets is None:
        presets = ["stock_preview", "thumbnail"]

    output_root = Path(output_root)
    results = []

    for rec in records:
        if rec.get("type") != "photo":
            continue
        if not rec.get("sellable", False):
            continue  # 解像度不足はスキップ

        src = Path(rec["path"])
        row = {"source": str(src), "outputs": {}, "error": None}
        for preset in presets:
            preset_dir = output_root / preset
            try:
                out = process_photo(src, preset_dir, preset, watermark_text)
                row["outputs"][preset] = str(out)
            except Exception as e:
                row["error"] = str(e)
        results.append(row)

    return results
