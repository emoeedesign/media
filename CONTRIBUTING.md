# コントリビューションガイド / AI協働ルール

このプロジェクトは **Codex（設計相談）** と **Claude Code（実装）** を使い分けるワークフローで開発します。
GitHubをコンテキスト共有のハブとして使うことで、AIツール間の引き継ぎをスムーズにします。

---

## 役割分担

| ツール | 主な用途 |
|--------|----------|
| **Codex** | 設計相談・アーキテクチャ議論・アイデア出し |
| **Claude Code** | 実装・デバッグ・テスト・git操作 |
| **GitHub Issues** | 設計決定の記録・タスク管理 |
| **docs/decisions/** | 重要な設計決定の永続的な記録（ADR） |

---

## 開発フロー

```
1. Codexで設計相談
      ↓
2. 相談内容をGitHub Issueに記録（設計相談テンプレートを使用）
      ↓
3. Claude CodeがIssueを参照して実装
      ↓
4. PRを作成・マージ
      ↓
5. 重要な決定はdocs/decisions/にADRとして保存
```

---

## Issueの使い方

### 設計相談Issue

- **テンプレート**: `設計相談` を選択
- Codexとの議論サマリーをそのまま貼る
- 決定事項と実装タスクを明記する
- ラベル: `design`

### Claude Codeへの指示

Issueに実装タスクを書いておくことで、Claude Codeは以下のように参照できる：

```
「Issue #XX を見て実装して」
```

---

## ブランチ命名規則

```
claude/<機能名>-<セッションID>   # Claude Codeが作業するブランチ
codex/<機能名>                   # Codexが提案したブランチ（手動作成）
feature/<機能名>                 # 一般的な機能追加
fix/<バグ内容>                   # バグ修正
```

---

## ADR（設計決定記録）

重要な設計決定は `docs/decisions/` に記録する。

- ファイル名: `YYYYMMDD-タイトル.md`
- テンプレートとインデックスは `docs/decisions/README.md` 参照

**記録すべき決定の例:**
- アーキテクチャの変更
- 外部APIやライブラリの採用・変更
- データ構造の設計
- AIエージェントの呼び出し方式

---

## AIツールへの引き継ぎ方

### Codex → Claude Code

1. CodexとのやりとりをGitHub Issueに貼る
2. Claude Codeに「Issue #XX を見て」と伝える

### Claude Code → Codex

1. 実装中に気づいた設計上の疑問をIssueにコメント
2. PRの「Claude Code / Codex メモ」欄に引き継ぎ事項を記載
3. Codexに「このリポジトリのIssue #XX を確認して」と伝える

---

## コミットメッセージ規則

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
refactor: リファクタリング
test: テスト追加・修正
chore: 設定・ツール変更
```
