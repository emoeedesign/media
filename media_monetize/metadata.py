"""
Metadata Manager - ストックサイト向けメタデータ管理
Shutterstock / Adobe Stock / Getty / PIXTA などへの CSV エクスポートをサポート
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict


@dataclass
class MediaMeta:
    """1メディアアイテムのメタデータ。"""
    filename: str
    title: str = ""
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    category: str = ""          # 例: "Nature", "Business", "Travel"
    subcategory: str = ""
    editorial: bool = False     # 編集用途のみ (商用不可)
    model_release: bool = False # 人物が写っている場合は True にして契約書を添付
    property_release: bool = False
    location: str = ""
    credit: str = ""
    copyright_notice: str = ""
    usage_terms: str = "Royalty-free"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["keywords"] = ", ".join(self.keywords)
        return d


# ---- ストックサイト別 CSV フォーマット -----------------------------------------------

SHUTTERSTOCK_FIELDS = [
    "Filename", "Description", "Keywords", "Categories", "EditorialUseOnly",
    "ModelReleased", "PropertyReleased",
]

ADOBE_STOCK_FIELDS = [
    "Filename", "Title", "Keywords", "Category", "Releases",
]

PIXTA_FIELDS = [
    "ファイル名", "タイトル", "説明文", "キーワード", "カテゴリ",
    "モデルリリース", "プロパティリリース",
]


def export_shutterstock_csv(items: list[MediaMeta], output: str | Path) -> Path:
    """Shutterstock 形式の CSV を生成する。"""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SHUTTERSTOCK_FIELDS)
        writer.writeheader()
        for m in items:
            writer.writerow({
                "Filename": m.filename,
                "Description": m.description or m.title,
                "Keywords": ", ".join(m.keywords),
                "Categories": m.category,
                "EditorialUseOnly": "yes" if m.editorial else "no",
                "ModelReleased": "yes" if m.model_release else "no",
                "PropertyReleased": "yes" if m.property_release else "no",
            })
    return output


def export_adobe_stock_csv(items: list[MediaMeta], output: str | Path) -> Path:
    """Adobe Stock 形式の CSV を生成する。"""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ADOBE_STOCK_FIELDS)
        writer.writeheader()
        for m in items:
            releases = []
            if m.model_release:
                releases.append("Model")
            if m.property_release:
                releases.append("Property")
            writer.writerow({
                "Filename": m.filename,
                "Title": m.title,
                "Keywords": ", ".join(m.keywords),
                "Category": m.category,
                "Releases": "; ".join(releases),
            })
    return output


def export_pixta_csv(items: list[MediaMeta], output: str | Path) -> Path:
    """PIXTA 形式の CSV を生成する。"""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8-sig") as f:  # BOM 付き
        writer = csv.DictWriter(f, fieldnames=PIXTA_FIELDS)
        writer.writeheader()
        for m in items:
            writer.writerow({
                "ファイル名": m.filename,
                "タイトル": m.title,
                "説明文": m.description,
                "キーワード": ", ".join(m.keywords),
                "カテゴリ": m.category,
                "モデルリリース": "あり" if m.model_release else "なし",
                "プロパティリリース": "あり" if m.property_release else "なし",
            })
    return output


def load_metadata_json(path: str | Path) -> list[MediaMeta]:
    """JSON ファイルからメタデータを読み込む。"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for d in data:
        kw = d.get("keywords", [])
        if isinstance(kw, str):
            kw = [k.strip() for k in kw.split(",") if k.strip()]
        items.append(MediaMeta(
            filename=d.get("filename", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            keywords=kw,
            category=d.get("category", ""),
            subcategory=d.get("subcategory", ""),
            editorial=d.get("editorial", False),
            model_release=d.get("model_release", False),
            property_release=d.get("property_release", False),
            location=d.get("location", ""),
            credit=d.get("credit", ""),
            copyright_notice=d.get("copyright_notice", ""),
        ))
    return items


def save_metadata_json(items: list[MediaMeta], path: str | Path) -> None:
    """メタデータを JSON ファイルに保存する。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = []
    for m in items:
        d = asdict(m)
        data.append(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_template_from_scan(
    scan_records: list[dict],
    output: str | Path,
    auto_genre: bool = False,
    force_genre: str | None = None,
) -> list[MediaMeta]:
    """
    スキャン結果からメタデータテンプレートを生成して JSON に保存する。

    Args:
        scan_records: scan_to_json() の出力
        output: 保存先 JSON パス
        auto_genre: True のとき、ファイル名からジャンルを推定してキーワードを自動付与
        force_genre: このジャンルを全ファイルに強制適用（auto_genre より優先）
    """
    items = []
    for r in scan_records:
        if not r.get("sellable", False):
            continue

        genre = force_genre or (suggest_genre(r["filename"]) if auto_genre else None)
        tmpl = GENRE_KEYWORD_TEMPLATES.get(genre, {}) if genre else {}

        keywords: list[str] = tmpl.get("en", []) + tmpl.get("ja", [])
        category: str = tmpl.get("category", "")
        model_release: bool = tmpl.get("model_release", False)

        items.append(MediaMeta(
            filename=r["filename"],
            title="",
            description="",
            keywords=keywords,
            category=category,
            model_release=model_release,
            copyright_notice="© " + r.get("camera", "").split()[0] if r.get("camera") else "",
        ))
    save_metadata_json(items, output)
    return items


# ---- 収益性チェック ----------------------------------------------------------------

MAJOR_STOCK_SITES = [
    {"name": "Shutterstock", "url": "https://submit.shutterstock.com", "royalty_pct": "15-40%"},
    {"name": "Adobe Stock", "url": "https://contributor.stock.adobe.com", "royalty_pct": "33%"},
    {"name": "Getty Images / iStock", "url": "https://www.gettyimages.com/contributor", "royalty_pct": "15-45%"},
    {"name": "PIXTA", "url": "https://pixta.jp/contributor", "royalty_pct": "42-53%"},
    {"name": "Pond5", "url": "https://www.pond5.com/sell-stock-footage", "royalty_pct": "35-60% (動画)"},
    {"name": "Dreamstime", "url": "https://www.dreamstime.com/sell-stock-photos", "royalty_pct": "25-60%"},
]


# ---- ジャンル別キーワードテンプレート -----------------------------------------------

GENRE_KEYWORD_TEMPLATES: dict[str, dict] = {
    "ice_climbing": {
        "en": [
            "ice climbing", "frozen waterfall", "winter mountaineering",
            "extreme sports", "alpinism", "ice axe", "crampon",
            "Japan winter", "adventure", "alpine climbing",
        ],
        "ja": [
            "アイスクライミング", "凍瀑", "冬山", "登山",
            "アルパインクライミング", "冬山登山", "極限スポーツ",
        ],
        "category": "Sports",
        "recommended_platforms": ["Getty Images / iStock", "Shutterstock", "Adobe Stock"],
        "model_release": True,
        "note": "人物が認識可能な場合はモデルリリース必須",
    },
    "juhyo_winter": {
        "en": [
            "juhyo", "snow monsters", "Zao", "Japan winter", "ski resort",
            "snowshoe", "mountain panorama", "winter landscape",
            "frost trees", "inbound travel Japan",
        ],
        "ja": [
            "樹氷", "蔵王", "山形", "冬景色", "スノーシュー",
            "雪山", "日本の冬", "絶景", "スキーリゾート",
        ],
        "category": "Nature",
        "recommended_platforms": ["PIXTA", "Getty Images / iStock", "Adobe Stock"],
        "model_release": False,
        "note": "後ろ姿のみの人物はリリース不要のケースが多いが要確認",
    },
    "onsen_lifestyle": {
        "en": [
            "Japan winter", "onsen town", "hot spring", "steam", "snowy stream",
            "backlight", "lens flare", "travel lifestyle",
            "man in snow", "Japanese culture",
        ],
        "ja": [
            "温泉", "雪景色", "冬の旅行", "湯煙", "逆光",
            "日本の冬", "ライフスタイル", "温泉街", "旅行",
        ],
        "category": "Travel",
        "recommended_platforms": ["Adobe Stock", "PIXTA", "Shutterstock"],
        "model_release": True,
        "note": "人物が画面中央・認識可能なためモデルリリース必須",
    },
}

_GENRE_FILENAME_HINTS: dict[str, list[str]] = {
    "ice_climbing": ["ice", "climb", "frozen", "waterfall", "axe", "crampon"],
    "juhyo_winter": ["juhyo", "snow", "zao", "frost", "monster", "snowshoe", "ski"],
    "onsen_lifestyle": ["onsen", "hotspring", "steam", "lifestyle", "travel"],
}


def suggest_genre(filename: str) -> str | None:
    """
    ファイル名からジャンルを推定する。

    Args:
        filename: 元のファイル名（例: "ice_axe_photo.jpg"）

    Returns:
        マッチしたジャンルキー、または None
    """
    lower = filename.lower()
    for genre, hints in _GENRE_FILENAME_HINTS.items():
        if any(hint in lower for hint in hints):
            return genre
    return None


def monetization_report(scan_records: list[dict]) -> dict:
    """スキャン結果からマネタイズ可能性レポートを生成する。"""
    photos = [r for r in scan_records if r.get("type") == "photo"]
    videos = [r for r in scan_records if r.get("type") == "video"]
    sellable_photos = [r for r in photos if r.get("sellable")]
    sellable_videos = [r for r in videos if r.get("sellable")]

    return {
        "total_files": len(scan_records),
        "photos": {
            "total": len(photos),
            "sellable": len(sellable_photos),
            "too_small": len(photos) - len(sellable_photos),
        },
        "videos": {
            "total": len(videos),
            "sellable": len(sellable_videos),
            "too_short": len(videos) - len(sellable_videos),
        },
        "recommended_platforms": MAJOR_STOCK_SITES,
        "tips": [
            "写真は最低 4MP 以上・ノイズが少なく鮮明なものを選ぶ",
            "同じ構図でも縦・横・正方形バリエーションを用意すると採用率UP",
            "動画は最低 5 秒・1080p 以上が望ましい",
            "人物が映る場合はモデルリリース契約書が必要",
            "建物・ブランド品が映る場合はプロパティリリースが必要",
            "キーワードは 10〜50 個が目安 (英語・日本語どちらも推奨)",
        ],
    }
