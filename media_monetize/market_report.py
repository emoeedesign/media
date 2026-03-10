"""
Market Report - ジャンル別ストック写真市場分析レポート
2026年時点の市場データに基づく収益性・プラットフォーム推奨情報を提供する
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ---------------------------------------------------------------------------
# 市場データ定数
# ---------------------------------------------------------------------------

MARKET_DATA = {
    "global_market_size_usd_b": 6.1,         # 2025年 グローバル市場規模 (十億ドル)
    "global_market_size_2030_usd_b": 10.1,   # 2030年予測
    "yoy_growth_pct": 10.9,
    "royalty_free_share_pct": 72.4,
    "avg_income_per_image_per_year_usd": 1.0,
    "top_creator_income_per_image_per_month_usd": 87.7,
}

PLATFORM_DETAILS: list[dict] = [
    {
        "name": "PIXTA",
        "royalty_pct": "20-53%",
        "specialty": "日本市場最大・日本語メタデータ対応",
        "best_genres": ["juhyo_winter", "onsen_lifestyle"],
        "url": "https://pixta.jp/contributor",
    },
    {
        "name": "Getty Images / iStock",
        "royalty_pct": "15-45%",
        "specialty": "高単価・プレミアム需要",
        "best_genres": ["ice_climbing", "juhyo_winter"],
        "url": "https://www.gettyimages.com/contributor",
    },
    {
        "name": "Adobe Stock",
        "royalty_pct": "33%",
        "specialty": "ライフスタイル系が強い",
        "best_genres": ["onsen_lifestyle", "juhyo_winter"],
        "url": "https://contributor.stock.adobe.com",
    },
    {
        "name": "Shutterstock",
        "royalty_pct": "15-40%",
        "specialty": "最大グローバルマーケット・量で稼ぐ",
        "best_genres": ["ice_climbing", "onsen_lifestyle"],
        "url": "https://submit.shutterstock.com",
    },
    {
        "name": "Pond5",
        "royalty_pct": "35-60%",
        "specialty": "動画コンテンツ特化",
        "best_genres": [],
        "url": "https://www.pond5.com/sell-stock-footage",
    },
    {
        "name": "Dreamstime",
        "royalty_pct": "25-60%",
        "specialty": "中規模・幅広いジャンル",
        "best_genres": [],
        "url": "https://www.dreamstime.com/sell-stock-photos",
    },
]

GENRE_MARKET_INFO: dict[str, dict] = {
    "ice_climbing": {
        "label": "アイスクライミング（凍瀑）",
        "competition": "中程度 (iStock 約8,600件)",
        "demand": "アウトドアブランド・山岳雑誌・アドベンチャー系メディア",
        "key_buyers": ["Arc'teryx", "Petzl", "Black Diamond", "National Geographic系"],
        "license_note": "商用利用にはモデルリリース必須（クライマーが認識可能）",
        "price_potential": "高 (Getty/Shutterstock Editorial + Commercial)",
        "priority_platforms": ["Getty Images / iStock", "Shutterstock", "Adobe Stock"],
    },
    "juhyo_winter": {
        "label": "樹氷・山頂パノラマ（蔵王・山形）",
        "competition": "比較的希少 (Getty: Snow Monsters 約1,081枚)",
        "demand": "日本観光・インバウンド・スキーリゾート広告で旺盛",
        "key_buyers": ["観光庁・自治体", "スキーリゾート", "旅行誌", "インバウンド旅行代理店"],
        "license_note": "後ろ姿のみの人物はリリース不要のケースあり（要判断）",
        "price_potential": "高 (日本市場・インバウンド需要)",
        "priority_platforms": ["PIXTA", "Getty Images / iStock", "Adobe Stock"],
    },
    "onsen_lifestyle": {
        "label": "温泉街・冬の渓流（人物・逆光）",
        "competition": "希少（湯煙＋雪＋逆光の組み合わせは独自性高い）",
        "demand": "旅行ライフスタイル・ファッション・日本文化系コンテンツ",
        "key_buyers": ["旅行雑誌", "観光PR", "ファッション/ライフスタイルブランド"],
        "license_note": "人物が画面中央・認識可能なためモデルリリース必須",
        "price_potential": "高 (モデルリリース取得時は3〜5倍の収益増)",
        "priority_platforms": ["Adobe Stock", "PIXTA", "Shutterstock"],
    },
}

MODEL_RELEASE_TABLE = [
    {
        "photo": "アイスクライミング",
        "recognizable": "高（カラフルウェア）",
        "without_release": "Editorial のみ",
        "with_release": "商用フル解放",
    },
    {
        "photo": "山頂パノラマ",
        "recognizable": "中（後ろ姿）",
        "without_release": "Editorial + 場合により商用",
        "with_release": "商用フル解放",
    },
    {
        "photo": "温泉街の人物",
        "recognizable": "高（中央・全身）",
        "without_release": "Editorial のみ",
        "with_release": "商用フル解放",
    },
]


# ---------------------------------------------------------------------------
# 分析関数
# ---------------------------------------------------------------------------

def genre_market_analysis(genre: str) -> dict:
    """
    指定ジャンルの市場分析データを返す。

    Args:
        genre: "ice_climbing" / "juhyo_winter" / "onsen_lifestyle"

    Returns:
        市場分析データの dict。不明ジャンルの場合は空 dict。
    """
    from media_monetize.metadata import GENRE_KEYWORD_TEMPLATES

    info = GENRE_MARKET_INFO.get(genre, {})
    kw_data = GENRE_KEYWORD_TEMPLATES.get(genre, {})
    if not info:
        return {}

    platforms = [
        p for p in PLATFORM_DETAILS
        if p["name"] in info.get("priority_platforms", [])
    ]

    return {
        "genre": genre,
        "label": info.get("label", genre),
        "market_info": info,
        "keywords": kw_data,
        "recommended_platforms": platforms,
        "global_market": MARKET_DATA,
    }


def print_market_report(
    scan_records: list[dict] | None = None,
    genres: list[str] | None = None,
    console: "Console | None" = None,
) -> None:
    """
    市場分析レポートを Rich テーブルで表示する。

    Args:
        scan_records: スキャン結果（省略可）
        genres:       表示するジャンルのリスト。省略時は全ジャンル表示。
        console:      Rich Console（省略時は新規作成）
    """
    if console is None:
        console = Console()

    if genres is None:
        genres = list(GENRE_MARKET_INFO.keys())

    # ---- グローバル市場概要 ----
    console.rule("[bold cyan]ストック写真 グローバル市場概要")
    market_table = Table(show_header=True, header_style="bold magenta")
    market_table.add_column("指標", style="cyan")
    market_table.add_column("値", justify="right", style="green")

    market_table.add_row("2025年 市場規模", f"${MARKET_DATA['global_market_size_usd_b']}B")
    market_table.add_row("2030年 予測市場規模", f"${MARKET_DATA['global_market_size_2030_usd_b']}B")
    market_table.add_row("前年比成長率", f"+{MARKET_DATA['yoy_growth_pct']}%")
    market_table.add_row("ロイヤリティフリー比率", f"{MARKET_DATA['royalty_free_share_pct']}%")
    market_table.add_row("業界平均収益/枚/年", f"${MARKET_DATA['avg_income_per_image_per_year_usd']}")
    market_table.add_row("上位クリエイター収益/枚/月", f"${MARKET_DATA['top_creator_income_per_image_per_month_usd']}")
    console.print(market_table)

    # ---- ジャンル別分析 ----
    for genre in genres:
        analysis = genre_market_analysis(genre)
        if not analysis:
            console.print(f"[yellow]警告:[/yellow] 不明なジャンル: {genre}")
            continue

        info = analysis["market_info"]
        kw = analysis.get("keywords", {})

        console.print()
        console.rule(f"[bold yellow]{analysis['label']}")

        detail_table = Table(show_header=False, box=None, padding=(0, 1))
        detail_table.add_column("項目", style="dim", min_width=20)
        detail_table.add_column("内容")

        detail_table.add_row("競合状況", info.get("competition", "—"))
        detail_table.add_row("主な需要", info.get("demand", "—"))
        detail_table.add_row("主要バイヤー", ", ".join(info.get("key_buyers", [])))
        detail_table.add_row("収益ポテンシャル", f"[green]{info.get('price_potential', '—')}[/green]")
        detail_table.add_row(
            "モデルリリース",
            f"[{'red' if 'モデルリリース必須' in info.get('license_note','') else 'yellow'}]{info.get('license_note', '—')}[/]"
        )
        console.print(detail_table)

        # 推奨プラットフォーム
        plat_table = Table(title="推奨プラットフォーム", show_header=True,
                           header_style="bold blue")
        plat_table.add_column("プラットフォーム", style="cyan")
        plat_table.add_column("ロイヤリティ", style="green")
        plat_table.add_column("特徴")
        for p in analysis["recommended_platforms"]:
            plat_table.add_row(p["name"], p["royalty_pct"], p["specialty"])
        console.print(plat_table)

        # キーワード
        en_kw = ", ".join(kw.get("en", [])[:8])
        ja_kw = ", ".join(kw.get("ja", [])[:6])
        console.print(Panel(
            f"[bold]英語:[/bold] {en_kw}\n[bold]日本語:[/bold] {ja_kw}",
            title="推奨キーワード（抜粋）",
            border_style="dim",
        ))

    # ---- モデルリリース戦略まとめ ----
    console.print()
    console.rule("[bold cyan]モデルリリース戦略まとめ")
    release_table = Table(show_header=True, header_style="bold magenta")
    release_table.add_column("写真", style="cyan")
    release_table.add_column("人物の認識可能性")
    release_table.add_column("リリースなし", style="yellow")
    release_table.add_column("リリースあり", style="green")

    for row in MODEL_RELEASE_TABLE:
        release_table.add_row(
            row["photo"], row["recognizable"],
            row["without_release"], row["with_release"],
        )
    console.print(release_table)

    console.print(Panel(
        "[yellow]推奨アクション:[/yellow] モデルリリース契約書を取得することで、\n"
        "収益が [green bold]3〜5倍[/green bold] になる可能性があります。",
        border_style="yellow",
    ))

    # ---- プラットフォーム優先度 ----
    console.print()
    console.rule("[bold cyan]推奨プラットフォーム 優先順位")
    priority_table = Table(show_header=True, header_style="bold blue")
    priority_table.add_column("順位", justify="center")
    priority_table.add_column("プラットフォーム", style="cyan")
    priority_table.add_column("ロイヤリティ", style="green")
    priority_table.add_column("強み")
    priority_table.add_column("URL", style="dim")

    for i, p in enumerate(PLATFORM_DETAILS, 1):
        priority_table.add_row(
            str(i), p["name"], p["royalty_pct"], p["specialty"], p["url"]
        )
    console.print(priority_table)
