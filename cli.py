#!/usr/bin/env python3
"""
Media Monetize CLI
ローカルの写真・動画をスキャンし、マネタイズ準備を行うコマンドラインツール

使い方:
  python cli.py scan   ./my_photos  --output scan_results.json
  python cli.py report scan_results.json
  python cli.py process scan_results.json --output-dir ./processed
  python cli.py meta   scan_results.json --output metadata/
  python cli.py portfolio scan_results.json --output-dir ./portfolio
  python cli.py run-all ./my_photos --output-dir ./out
"""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


@click.group()
def cli():
    """メディアマネタイズツールキット"""


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("media_dir", type=click.Path(exists=True))
@click.option("--output", "-o", default="scan_results.json", show_default=True,
              help="スキャン結果 JSON の出力先")
@click.option("--no-recursive", is_flag=True, default=False,
              help="サブディレクトリを再帰スキャンしない")
def scan(media_dir, output, no_recursive):
    """指定ディレクトリの写真・動画をスキャンする"""
    from media_monetize.scanner import scan_to_json

    console.rule("[bold cyan]メディアスキャン開始")
    with console.status(f"[cyan]スキャン中: {media_dir}"):
        results = scan_to_json(media_dir, output, recursive=not no_recursive)

    photos = [r for r in results if r["type"] == "photo"]
    videos = [r for r in results if r["type"] == "video"]
    console.print(f"[green]完了[/green] {len(results)} ファイルを検出")
    console.print(f"  写真: {len(photos)}  動画: {len(videos)}")
    console.print(f"  出力: [bold]{output}[/bold]")


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("scan_json", type=click.Path(exists=True))
def report(scan_json):
    """スキャン結果のマネタイズレポートを表示する"""
    from media_monetize.metadata import monetization_report

    with open(scan_json, encoding="utf-8") as f:
        records = json.load(f)

    rep = monetization_report(records)

    console.rule("[bold cyan]マネタイズレポート")

    # 統計テーブル
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("カテゴリ", style="cyan")
    table.add_column("総数", justify="right")
    table.add_column("販売可能", justify="right", style="green")
    table.add_column("除外", justify="right", style="yellow")

    p = rep["photos"]
    v = rep["videos"]
    table.add_row("写真", str(p["total"]), str(p["sellable"]), str(p["too_small"]))
    table.add_row("動画", str(v["total"]), str(v["sellable"]), str(v["too_short"]))
    console.print(table)

    # プラットフォーム一覧
    console.print()
    plat_table = Table(title="主要販売プラットフォーム", show_header=True, header_style="bold blue")
    plat_table.add_column("サービス")
    plat_table.add_column("ロイヤリティ", style="green")
    plat_table.add_column("URL", style="dim")
    for p in rep["recommended_platforms"]:
        plat_table.add_row(p["name"], p["royalty_pct"], p["url"])
    console.print(plat_table)

    # Tips
    console.print()
    tips_text = "\n".join(f"• {t}" for t in rep["tips"])
    console.print(Panel(tips_text, title="[bold]販売Tips", border_style="yellow"))


# ---------------------------------------------------------------------------
# process
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("scan_json", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="processed", show_default=True)
@click.option("--presets", "-p", default="stock_preview,thumbnail", show_default=True,
              help="カンマ区切りのプリセット名 (stock_full/stock_preview/web_medium/thumbnail)")
@click.option("--watermark", "-w", default="© PREVIEW", show_default=True)
def process(scan_json, output_dir, presets, watermark):
    """写真をウォーターマーク付きでリサイズ・変換する"""
    from media_monetize.processor import batch_process_photos

    with open(scan_json, encoding="utf-8") as f:
        records = json.load(f)

    preset_list = [p.strip() for p in presets.split(",")]
    console.rule("[bold cyan]メディア処理開始")

    with console.status("[cyan]処理中..."):
        results = batch_process_photos(records, output_dir, preset_list, watermark)

    ok = [r for r in results if not r["error"]]
    ng = [r for r in results if r["error"]]
    console.print(f"[green]成功[/green]: {len(ok)}  [red]失敗[/red]: {len(ng)}")
    for r in ng:
        console.print(f"  [red]ERROR[/red] {r['source']}: {r['error']}")
    console.print(f"  出力先: [bold]{output_dir}[/bold]")


# ---------------------------------------------------------------------------
# meta
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("scan_json", type=click.Path(exists=True))
@click.option("--output", "-o", default="metadata/template.json", show_default=True,
              help="メタデータテンプレート JSON の出力先")
@click.option("--format", "-f", "fmt",
              type=click.Choice(["shutterstock", "adobe", "pixta", "all"]),
              default="all", show_default=True)
@click.option("--meta-json", default=None,
              help="編集済みメタデータ JSON (未指定時はテンプレートのみ生成)")
@click.option("--auto-genre", is_flag=True, default=False,
              help="ファイル名からジャンルを自動推定してキーワードを付与する")
@click.option("--genre", default=None,
              type=click.Choice(["ice_climbing", "juhyo_winter", "onsen_lifestyle"]),
              help="全ファイルに適用するジャンルを指定（--auto-genre より優先）")
def meta(scan_json, output, fmt, meta_json, auto_genre, genre):
    """メタデータテンプレートを生成 / ストックサイト用 CSV をエクスポート

    \b
    基本的な使い方:
      python cli.py meta scan_results.json

    \b
    ジャンル自動検出（ファイル名からキーワードを推定）:
      python cli.py meta scan_results.json --auto-genre

    \b
    ジャンルを固定（全ファイルに同じキーワードを付与）:
      python cli.py meta scan_results.json --genre juhyo_winter
    """
    from media_monetize.metadata import (
        generate_template_from_scan, load_metadata_json,
        export_shutterstock_csv, export_adobe_stock_csv, export_pixta_csv,
        GENRE_KEYWORD_TEMPLATES,
    )

    with open(scan_json, encoding="utf-8") as f:
        records = json.load(f)

    console.rule("[bold cyan]メタデータ処理")

    if meta_json is None:
        items = generate_template_from_scan(
            records, output,
            auto_genre=auto_genre,
            force_genre=genre,
        )
        console.print(f"[green]テンプレート生成完了[/green]: {len(items)} 件 → {output}")

        if genre or auto_genre:
            genres_applied = {}
            for item in items:
                g = genre or "auto"
                genres_applied.setdefault(g, 0)
                genres_applied[g] += 1
            auto_count = sum(1 for item in items if item.keywords)
            console.print(f"  [cyan]キーワード自動付与[/cyan]: {auto_count}/{len(items)} 件")
            if genre and genre in GENRE_KEYWORD_TEMPLATES:
                tmpl = GENRE_KEYWORD_TEMPLATES[genre]
                kw_count = len(tmpl.get("en", [])) + len(tmpl.get("ja", []))
                console.print(f"  ジャンル [bold]{genre}[/bold]: {kw_count} キーワード / 件")
                if tmpl.get("model_release"):
                    console.print(f"  [yellow]⚠[/yellow]  model_release = True が設定されました（人物撮影の場合は書類を取得してください）")
        else:
            console.print("[yellow]ヒント[/yellow]: JSON を編集してタイトル・キーワードを記入してください")
            console.print("  ジャンル自動検出を使う場合は [bold]--auto-genre[/bold] を追加してください")
        return

    items = load_metadata_json(meta_json)
    out_dir = Path(output).parent

    if fmt in ("shutterstock", "all"):
        p = export_shutterstock_csv(items, out_dir / "shutterstock.csv")
        console.print(f"[green]Shutterstock CSV[/green]: {p}")
    if fmt in ("adobe", "all"):
        p = export_adobe_stock_csv(items, out_dir / "adobe_stock.csv")
        console.print(f"[green]Adobe Stock CSV[/green]: {p}")
    if fmt in ("pixta", "all"):
        p = export_pixta_csv(items, out_dir / "pixta.csv")
        console.print(f"[green]PIXTA CSV[/green]: {p}")


# ---------------------------------------------------------------------------
# portfolio
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("scan_json", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="portfolio", show_default=True)
@click.option("--title", "-t", default="My Media Portfolio", show_default=True,
              help="単一ページモード時のページタイトル")
@click.option("--thumb-dir", default=None,
              help="サムネイル画像ディレクトリ (processed/thumbnail など)")
# ---- マルチページサイト生成オプション ----
@click.option("--multi-page", is_flag=True, default=False,
              help="マルチページのフォトグラファーサイトを生成する")
@click.option("--site-name", default="My Portfolio", show_default=True,
              help="サイト名（ナビ・フッターに表示）")
@click.option("--photographer", default="Photographer", show_default=True,
              help="撮影者名")
@click.option("--location", default="Japan", show_default=True,
              help="活動拠点")
@click.option("--tagline", default="写真でひとの心を動かす。", show_default=True,
              help="ヒーローセクションのキャッチコピー")
@click.option("--contact-email", default="contact@example.com", show_default=True,
              help="コンタクト用メールアドレス")
@click.option("--title-tag", default=None,
              help="SEOタイトルタグ（省略時は --site-name を使用）")
@click.option("--description", default="", help="SEOメタディスクリプション")
@click.option("--keywords", default="", help="SEOキーワード（カンマ区切り）")
@click.option("--generate-privacy/--no-privacy", default=True, show_default=True,
              help="プライバシーポリシーページを自動生成する")
def portfolio(scan_json, output_dir, title, thumb_dir,
              multi_page, site_name, photographer, location,
              tagline, contact_email, title_tag, description,
              keywords, generate_privacy):
    """HTML ポートフォリオを生成する

    \b
    単一ページモード（デフォルト）:
      python cli.py portfolio scan_results.json --thumb-dir ./processed/thumbnail

    \b
    マルチページサイト生成モード:
      python cli.py portfolio scan_results.json \\
        --multi-page \\
        --site-name "emoeedesign" \\
        --photographer "和也 / Kazuya" \\
        --location "東京・埼玉" \\
        --tagline "舞台・企業・アーティスト写真をワンストップで。" \\
        --contact-email "contact@emoeedesign.com" \\
        --title-tag "フォトグラファー 和也 | 舞台・企業・アーティスト撮影 | 東京・埼玉"
    """
    with open(scan_json, encoding="utf-8") as f:
        records = json.load(f)

    console.rule("[bold cyan]ポートフォリオ生成")

    if multi_page:
        from media_monetize.portfolio import generate_site
        generated = generate_site(
            records, output_dir,
            site_name=site_name,
            photographer=photographer,
            location=location,
            tagline=tagline,
            contact_email=contact_email,
            title_tag=title_tag,
            description=description,
            keywords=keywords,
            generate_privacy=generate_privacy,
            thumb_dir=thumb_dir,
        )
        console.print(f"[green]マルチページサイト生成完了[/green]  ({len(generated)} ページ)")
        for key, path in generated.items():
            console.print(f"  [cyan]{key:10}[/cyan] {path}")
        index = generated.get("index", Path(output_dir) / "index.html")
    else:
        from media_monetize.portfolio import generate_portfolio
        index = generate_portfolio(records, output_dir, title, thumb_dir=thumb_dir)
        console.print(f"[green]完了[/green]: {index}")

    console.print(f"  ブラウザで開く: [bold]open {index}[/bold]  (macOS) / [bold]xdg-open {index}[/bold]  (Linux)")


# ---------------------------------------------------------------------------
# market
# ---------------------------------------------------------------------------
@cli.command()
@click.option("--genre", "-g", multiple=True,
              type=click.Choice(["ice_climbing", "juhyo_winter", "onsen_lifestyle", "all"]),
              default=["all"], show_default=True,
              help="表示するジャンル（複数指定可）")
@click.option("--scan-json", default=None, type=click.Path(exists=True),
              help="スキャン結果 JSON（指定時はファイル数を市場分析に含める）")
def market(genre, scan_json):
    """ジャンル別ストック写真市場分析レポートを表示する

    \b
    使用例:
      python cli.py market --genre ice_climbing
      python cli.py market --genre juhyo_winter --genre onsen_lifestyle
      python cli.py market  # 全ジャンル表示
    """
    from media_monetize.market_report import print_market_report

    records = None
    if scan_json:
        with open(scan_json, encoding="utf-8") as f:
            records = json.load(f)

    genres_list = (
        ["ice_climbing", "juhyo_winter", "onsen_lifestyle"]
        if "all" in genre else list(genre)
    )

    console.rule("[bold cyan]ストック写真 市場分析レポート")
    print_market_report(scan_records=records, genres=genres_list, console=console)


# ---------------------------------------------------------------------------
# run-all  (ワンストップコマンド)
# ---------------------------------------------------------------------------
@cli.command("run-all")
@click.argument("media_dir", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="monetize_output", show_default=True)
@click.option("--title", "-t", default="My Media Portfolio", show_default=True)
@click.option("--watermark", "-w", default="© PREVIEW", show_default=True)
# ---- マルチページサイト生成オプション ----
@click.option("--multi-page", is_flag=True, default=False,
              help="マルチページのフォトグラファーサイトを生成する")
@click.option("--site-name", default=None,
              help="サイト名（省略時は --title を使用）")
@click.option("--photographer", default="Photographer", show_default=True,
              help="撮影者名")
@click.option("--location", default="Japan", show_default=True,
              help="活動拠点")
@click.option("--tagline", default="写真でひとの心を動かす。", show_default=True,
              help="ヒーローセクションのキャッチコピー")
@click.option("--contact-email", default="contact@example.com", show_default=True,
              help="コンタクト用メールアドレス")
@click.option("--title-tag", default=None,
              help="SEOタイトルタグ（省略時は --site-name を使用）")
@click.option("--generate-privacy/--no-privacy", default=True, show_default=True,
              help="プライバシーポリシーページを自動生成する")
def run_all(media_dir, output_dir, title, watermark,
            multi_page, site_name, photographer, location,
            tagline, contact_email, title_tag, generate_privacy):
    """スキャン→レポート→処理→ポートフォリオをまとめて実行する

    \b
    単一ページモード（デフォルト）:
      python cli.py run-all ./my_photos

    \b
    マルチページサイト生成モード:
      python cli.py run-all ./my_photos \\
        --multi-page \\
        --site-name "emoeedesign" \\
        --photographer "和也 / Kazuya" \\
        --location "東京・埼玉" \\
        --tagline "舞台・企業・アーティスト写真をワンストップで。" \\
        --contact-email "contact@emoeedesign.com"
    """
    from media_monetize.scanner import scan_to_json
    from media_monetize.metadata import monetization_report, generate_template_from_scan
    from media_monetize.processor import batch_process_photos

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    console.rule("[bold cyan]Step 1/4: スキャン")
    scan_json = out / "scan_results.json"
    with console.status("[cyan]スキャン中..."):
        records = scan_to_json(media_dir, scan_json)
    console.print(f"[green]スキャン完了[/green]: {len(records)} ファイル")

    console.rule("[bold cyan]Step 2/4: レポート")
    rep = monetization_report(records)
    console.print(f"  販売可能写真: {rep['photos']['sellable']}")
    console.print(f"  販売可能動画: {rep['videos']['sellable']}")

    console.rule("[bold cyan]Step 3/4: 写真処理 (プレビュー + サムネイル)")
    processed = out / "processed"
    with console.status("[cyan]処理中..."):
        results = batch_process_photos(
            records, processed,
            ["stock_preview", "thumbnail"],
            watermark,
        )
    console.print(f"[green]処理完了[/green]: {len(results)} 件")

    console.rule("[bold cyan]Step 4/4: メタデータテンプレート + ポートフォリオ")
    generate_template_from_scan(records, out / "metadata" / "template.json")
    thumb_dir = processed / "thumbnail"

    if multi_page:
        from media_monetize.portfolio import generate_site
        generated = generate_site(
            records, out / "portfolio",
            site_name=site_name or title,
            photographer=photographer,
            location=location,
            tagline=tagline,
            contact_email=contact_email,
            title_tag=title_tag,
            generate_privacy=generate_privacy,
            thumb_dir=thumb_dir if thumb_dir.exists() else None,
        )
        index = generated.get("index", out / "portfolio" / "index.html")
        console.print(f"[green]マルチページサイト生成完了[/green] ({len(generated)} ページ)")
        for key, path in generated.items():
            console.print(f"  [cyan]{key:10}[/cyan] {path}")
    else:
        from media_monetize.portfolio import generate_portfolio
        index = generate_portfolio(
            records, out / "portfolio", title,
            thumb_dir=thumb_dir if thumb_dir.exists() else None,
        )

    next_steps = (
        f"  1. metadata/template.json を編集してタイトル・キーワードを記入\n"
        f"  2. python cli.py meta {scan_json} --meta-json metadata/template.json\n"
        f"  3. 生成された CSV を各ストックサイトへアップロード"
    )
    if not multi_page:
        next_steps += (
            f"\n\n[dim]マルチページサイトを生成するには --multi-page を追加してください[/dim]"
        )

    console.print()
    console.print(Panel(
        f"[green bold]すべての処理が完了しました![/green bold]\n\n"
        f"  スキャン結果:  {scan_json}\n"
        f"  処理済み写真:  {processed}\n"
        f"  メタデータ:    {out / 'metadata' / 'template.json'}\n"
        f"  ポートフォリオ: {index}\n\n"
        f"[yellow]次のステップ:[/yellow]\n"
        + next_steps,
        title="[bold]完了", border_style="green"
    ))


if __name__ == "__main__":
    cli()
