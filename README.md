# Media Monetize Toolkit

ローカルの写真・動画をスキャンし、ストックサイトで販売するための準備を自動化するツールキットです。

## 機能

| 機能 | 説明 |
|---|---|
| **スキャン** | ディレクトリを再帰的に検索し、写真・動画のメタ情報を収集 |
| **重複検出** | MD5 ハッシュで重複ファイルを検出 |
| **販売可否判定** | 写真は 4MP 以上、動画は 5 秒以上を「販売可能」とみなす |
| **ウォーターマーク** | プレビュー用に半透明テキストを配置 |
| **リサイズ** | ストックサイト納品用・Web用など目的別にリサイズ |
| **メタデータ管理** | Shutterstock / Adobe Stock / PIXTA 向け CSV を生成 |
| **HTMLポートフォリオ** | ブラウザで確認できる一覧ページを自動生成 |

## インストール

```bash
pip install -r requirements.txt
```

## クイックスタート

```bash
# ワンストップ実行（スキャン→処理→ポートフォリオ生成）
python cli.py run-all ./my_photos --output-dir ./out --title "My Portfolio"

# ポートフォリオを開く
open ./out/portfolio/index.html       # macOS
xdg-open ./out/portfolio/index.html   # Linux
```

## 個別コマンド

```bash
# 1. スキャン
python cli.py scan ./my_photos --output scan_results.json

# 2. レポート表示（販売可能ファイル数・プラットフォーム情報）
python cli.py report scan_results.json

# 3. 写真処理（ウォーターマーク付きプレビュー + サムネイル）
python cli.py process scan_results.json \
  --output-dir ./processed \
  --presets "stock_preview,thumbnail" \
  --watermark "© YourName"

# 4. メタデータテンプレート生成
python cli.py meta scan_results.json --output metadata/template.json

# 5. テンプレートを編集後、各サイト向け CSV をエクスポート
python cli.py meta scan_results.json \
  --meta-json metadata/template.json \
  --format all

# 6. HTMLポートフォリオ生成
python cli.py portfolio scan_results.json \
  --output-dir ./portfolio \
  --thumb-dir ./processed/thumbnail
```

## プリセット一覧

| プリセット名 | 用途 | サイズ |
|---|---|---|
| `stock_full` | ストックサイト納品用 | 長辺 6000px 以内, JPEG 品質 95 |
| `stock_preview` | ウォーターマーク付きプレビュー | 長辺 1200px, JPEG 品質 85 |
| `web_medium` | Web 掲載用 | 長辺 1920px, JPEG 品質 90 |
| `thumbnail` | サムネイル | 320×320 正方形クロップ |

## 対応プラットフォーム

- [Shutterstock](https://submit.shutterstock.com) — ロイヤリティ 15〜40%
- [Adobe Stock](https://contributor.stock.adobe.com) — ロイヤリティ 33%
- [Getty Images / iStock](https://www.gettyimages.com/contributor) — ロイヤリティ 15〜45%
- [PIXTA](https://pixta.jp/contributor) — ロイヤリティ 42〜53%（日本語メタデータ対応）
- [Pond5](https://www.pond5.com/sell-stock-footage) — 動画特化, ロイヤリティ 35〜60%
- [Dreamstime](https://www.dreamstime.com/sell-stock-photos) — ロイヤリティ 25〜60%

## メタデータ JSON フォーマット

```json
[
  {
    "filename": "DSC_0001.jpg",
    "title": "富士山の夕焼け",
    "description": "静岡県から望む富士山の夕焼け風景",
    "keywords": ["富士山", "夕焼け", "日本", "山", "自然", "Mt. Fuji", "sunset", "Japan"],
    "category": "Nature",
    "model_release": false,
    "property_release": false,
    "editorial": false,
    "location": "静岡県, 日本"
  }
]
```

## 販売のポイント

1. **写真は最低 4MP** — ノイズが少なく鮮明なものを選ぶ
2. **同じ構図でバリエーション** — 縦・横・正方形を用意すると採用率UP
3. **動画は最低 5 秒・1080p 以上** が望ましい
4. **人物が映る場合** はモデルリリース契約書が必要
5. **建物・ブランド品** が映る場合はプロパティリリースが必要
6. **キーワードは英語＋日本語両方** を 10〜50 個が目安

## ディレクトリ構成（run-all 実行後）

```
monetize_output/
├── scan_results.json          # スキャン結果
├── processed/
│   ├── stock_preview/         # ウォーターマーク付きプレビュー
│   └── thumbnail/             # サムネイル
├── metadata/
│   └── template.json          # 編集用メタデータテンプレート
└── portfolio/
    ├── index.html             # HTMLポートフォリオ
    └── thumbs/                # ポートフォリオ用サムネイル
```
