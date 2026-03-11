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
| **マルチページサイト生成** ⭐ | CTA・SEO・プライバシーポリシー・モバイル対応の完全サイトを生成 |
| **市場分析レポート** ⭐ | ジャンル別（樹氷・アイスクライミング等）の市場データ・キーワードを表示 |

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

## マルチページサイト生成 ⭐

ローカル写真からコンバージョン最適化済みの完全なフォトグラファーサイトを生成します。

**生成されるファイル構成:**

```
portfolio/
├── index.html          # トップページ（ヒーロー・CTA・各セクション・コンタクトフォーム）
├── portfolio.html      # ポートフォリオ一覧（モバイル2列グリッド対応）
├── works/
│   └── index.html      # ワークス一覧（カテゴリフィルター付き）
├── privacy.html        # プライバシーポリシー（自動生成）
└── thumbs/             # サムネイル画像
```

**主な特徴（emoeedesign.com 分析に基づく改善点を反映）:**

| 改善点 | 対応内容 |
|---|---|
| ファーストビューにCTAがない | ヒーローセクションに「撮影を相談する →」ボタンを追加 |
| プライバシーポリシーが空白 | `--generate-privacy` で内容付きページを自動生成 |
| 各ページ末尾にCTAがない | ポートフォリオ・ワークス末尾にCTAブロックを自動挿入 |
| スマホでグリッドが崩れる | `repeat(auto-fill, minmax(280px, 1fr))` で2列対応 |
| フォームに撮影種別がない | 撮影種別セレクト（舞台/企業/アーティスト/Web/その他）を追加 |
| SEOタイトルが英語のみ | `--title-tag` で日本語キーワード入りタイトルを設定可能 |

```bash
# 基本的なマルチページサイト生成
python cli.py portfolio scan_results.json \
  --multi-page \
  --thumb-dir ./processed/thumbnail \
  --site-name "emoeedesign" \
  --photographer "和也 / Kazuya" \
  --location "東京・埼玉" \
  --tagline "舞台・企業・アーティスト写真をワンストップで。" \
  --contact-email "contact@emoeedesign.com" \
  --title-tag "フォトグラファー 和也 | 舞台・企業・アーティスト撮影 | 東京・埼玉" \
  --generate-privacy
```

## 市場分析レポート ⭐

ジャンル別の市場規模・推奨プラットフォーム・キーワードを表示します。

```bash
# 全ジャンル表示
python cli.py market

# 特定ジャンルのみ
python cli.py market --genre ice_climbing
python cli.py market --genre juhyo_winter
python cli.py market --genre onsen_lifestyle

# 複数ジャンル指定
python cli.py market --genre ice_climbing --genre juhyo_winter
```

**対応ジャンル:**

| ジャンルキー | 内容 | 主要市場 |
|---|---|---|
| `ice_climbing` | アイスクライミング・凍瀑 | Getty Images, Shutterstock |
| `juhyo_winter` | 樹氷・山頂パノラマ（蔵王等） | PIXTA, Getty Images |
| `onsen_lifestyle` | 温泉街・冬の渓流（人物・逆光） | Adobe Stock, PIXTA |

## 販売のポイント

1. **写真は最低 4MP** — ノイズが少なく鮮明なものを選ぶ
2. **同じ構図でバリエーション** — 縦・横・正方形を用意すると採用率UP
3. **動画は最低 5 秒・1080p 以上** が望ましい
4. **人物が映る場合** はモデルリリース契約書が必要
5. **建物・ブランド品** が映る場合はプロパティリリースが必要
6. **キーワードは英語＋日本語両方** を 10〜50 個が目安

## ワンストップ実行（run-all）

スキャン・処理・メタデータ生成・ポートフォリオ生成をまとめて実行します。

```bash
# 単一ページモード（デフォルト）
python cli.py run-all ./my_photos

# マルチページサイト生成モード
python cli.py run-all ./my_photos \
  --multi-page \
  --site-name "emoeedesign" \
  --photographer "和也 / Kazuya" \
  --location "東京・埼玉" \
  --tagline "舞台・企業・アーティスト写真をワンストップで。" \
  --contact-email "contact@emoeedesign.com" \
  --title-tag "フォトグラファー 和也 | 舞台・企業・アーティスト撮影 | 東京・埼玉"
```

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
    ├── index.html             # HTMLポートフォリオ（単一ページモード）
    └── thumbs/                # ポートフォリオ用サムネイル
```

マルチページサイト生成（`--multi-page`）後のディレクトリ構成:

```
portfolio/
├── index.html                 # トップページ（ヒーロー・CTA・コンタクトフォーム）
├── portfolio.html             # ポートフォリオ一覧（モバイル2列グリッド）
├── works/
│   └── index.html             # ワークス一覧（カテゴリフィルター）
├── privacy.html               # プライバシーポリシー（自動生成）
└── thumbs/                    # サムネイル画像
```
