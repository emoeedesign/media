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
def meta(scan_json, output, fmt, meta_json):
    """メタデータテンプレートを生成 / ストックサイト用 CSV をエクスポート"""
    from media_monetize.metadata import (
        generate_template_from_scan, load_metadata_json,
        export_shutterstock_csv, export_adobe_stock_csv, export_pixta_csv,
    )

    with open(scan_json, encoding="utf-8") as f:
        records = json.load(f)

    console.rule("[bold cyan]メタデータ処理")

    if meta_json is None:
        items = generate_template_from_scan(records, output)
        console.print(f"[green]テンプレート生成完了[/green]: {len(items)} 件 → {output}")
        console.print("[yellow]ヒント[/yellow]: JSON を編集してタイトル・キーワードを記入してください")
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
@click.option("--title", "-t", default="My Media Portfolio", show_default=True)
@click.option("--thumb-dir", default=None,
              help="サムネイル画像ディレクトリ (processed/thumbnail など)")
def portfolio(scan_json, output_dir, title, thumb_dir):
    """HTML ポートフォリオを生成する"""
    from media_monetize.portfolio import generate_portfolio

    with open(scan_json, encoding="utf-8") as f:
        records = json.load(f)

    console.rule("[bold cyan]ポートフォリオ生成")
    index = generate_portfolio(records, output_dir, title, thumb_dir=thumb_dir)
    console.print(f"[green]完了[/green]: {index}")
    console.print(f"  ブラウザで開く: [bold]open {index}[/bold]  (macOS) / [bold]xdg-open {index}[/bold]  (Linux)")


# ---------------------------------------------------------------------------
# run-all  (ワンストップコマンド)
# ---------------------------------------------------------------------------
@cli.command("run-all")
@click.argument("media_dir", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="monetize_output", show_default=True)
@click.option("--title", "-t", default="My Media Portfolio", show_default=True)
@click.option("--watermark", "-w", default="© PREVIEW", show_default=True)
def run_all(media_dir, output_dir, title, watermark):
    """スキャン→レポート→処理→ポートフォリオをまとめて実行する"""
    from media_monetize.scanner import scan_to_json
    from media_monetize.metadata import monetization_report, generate_template_from_scan
    from media_monetize.processor import batch_process_photos
    from media_monetize.portfolio import generate_portfolio

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
    index = generate_portfolio(
        records, out / "portfolio", title,
        thumb_dir=thumb_dir if thumb_dir.exists() else None,
    )

    console.print()
    console.print(Panel(
        f"[green bold]すべての処理が完了しました![/green bold]\n\n"
        f"  スキャン結果:  {scan_json}\n"
        f"  処理済み写真:  {processed}\n"
        f"  メタデータ:    {out / 'metadata' / 'template.json'}\n"
        f"  ポートフォリオ: {index}\n\n"
        f"[yellow]次のステップ:[/yellow]\n"
        f"  1. metadata/template.json を編集してタイトル・キーワードを記入\n"
        f"  2. python cli.py meta scan_results.json --meta-json metadata/template.json\n"
        f"  3. 生成された CSV を各ストックサイトへアップロード",
        title="[bold]完了", border_style="green"
    ))


if __name__ == "__main__":
    cli()
