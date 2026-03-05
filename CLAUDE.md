# Investment_kota プロジェクト概要

## 設計方針

このシステムは**「自然言語ファースト」で設計**されています。
ユーザーは日本語で意図を伝えるだけで、適切なスキルが自動的に選択・実行されます。
コマンドはあくまで内部実装であり、自然言語からの意図推論が第一の入口です。

## プロジェクト概要

割安株スクリーニング・ポートフォリオ管理システムです。
Yahoo Finance API を使用して、日本株・米国株・ASEAN株・欧州株・香港株・韓国株・台湾株など60地域以上から割安銘柄をスクリーニングします。
Claude Code Skills として動作し、投資ワークフロー全体をカバーします。

## ディレクトリ構成

```
Investment_kota/
├── .claude/
│   ├── skills/           # 8つのスキル定義 (SKILL.md)
│   └── rules/            # intent-routing等のルール
├── config/
│   ├── screening_presets.yaml   # 15投資戦略プリセット
│   └── exchanges.yaml           # 60+地域取引所定義
├── src/
│   ├── core/             # ビジネスロジック層
│   │   ├── screening.py  # スクリーニングエンジン
│   │   ├── portfolio.py  # ポートフォリオ管理
│   │   ├── risk.py       # リスク分析・ストレステスト
│   │   └── research.py   # 銘柄調査・レポート生成
│   ├── data/             # データアクセス層
│   │   ├── yahoo_client.py  # Yahoo Finance APIクライアント (24時間キャッシュ)
│   │   └── cache.py         # JSONキャッシュ管理
│   └── output/           # 出力フォーマッタ層
│       ├── screening_formatter.py
│       ├── portfolio_formatter.py
│       └── report_formatter.py
├── scripts/              # スキル実行スクリプト
│   ├── screen_stocks.py
│   ├── stock_report.py
│   ├── watchlist.py
│   ├── stress_test.py
│   ├── portfolio.py
│   └── investment_note.py
├── data/                 # 永続化データ
│   ├── portfolio.csv     # ポートフォリオ売買記録
│   ├── watchlist.csv     # ウォッチリスト
│   └── notes/            # 投資メモ (Markdown)
├── tests/                # テストスイート
├── CLAUDE.md             # このファイル
├── README.md
├── requirements.txt
└── pytest.ini
```

## 3層アーキテクチャ

### Skills層 (`.claude/skills/*/SKILL.md`)
8つのスキルが自然言語の意図を解釈し、適切なPythonスクリプトを呼び出します。

| スキル | コマンド | 機能 |
|--------|----------|------|
| screen-stocks | `/screen-stocks` | 15プリセット×60地域の割安株スクリーニング |
| stock-report | `/stock-report` | 個別銘柄の詳細財務分析レポート |
| watchlist | `/watchlist` | ウォッチリスト管理（追加・削除・表示） |
| stress-test | `/stress-test` | 8シナリオのポートフォリオストレステスト |
| market-research | `/market-research` | 業界・銘柄・マーケットの深掘り調査 |
| stock-portfolio | `/stock-portfolio` | 売買記録・損益・HHI集中度・リバランス |
| investment-note | `/investment-note` | 投資テーゼ・懸念点のメモ管理 |
| graph-query | `/graph-query` | 分析履歴の横断検索 |

### Core層 (`src/core/`)
- `screening.py`: スクリーニングエンジン、スコアリング、フィルタリング
- `portfolio.py`: 売買記録、損益計算、HHI集中度、リバランス、複利シミュレーション
- `risk.py`: ストレステスト8シナリオ、ベータ計算、シャープレシオ、最大ドローダウン
- `research.py`: 財務指標取得、バリュートラップ判定、レポート生成

### Data層 (`src/data/`)
- `yahoo_client.py`: Yahoo Finance APIラッパー、24時間JSONキャッシュ
- `cache.py`: キャッシュ管理（読み書き・有効期限チェック）

### Output層 (`src/output/`)
- `screening_formatter.py`: スクリーニング結果をMarkdownテーブルで出力
- `portfolio_formatter.py`: ポートフォリオサマリー・損益レポート出力
- `report_formatter.py`: 個別銘柄レポートのMarkdown生成

## データ永続化戦略

| データ種別 | 保存形式 | 場所 |
|-----------|----------|------|
| ポートフォリオ売買記録 | CSV | `data/portfolio.csv` |
| ウォッチリスト | CSV | `data/watchlist.csv` |
| 投資メモ | Markdown | `data/notes/*.md` |
| APIキャッシュ | JSON | `data/cache/*.json` |
| 設定・閾値 | YAML | `config/*.yaml` |
| プロジェクト文脈 | Markdown | `CLAUDE.md` |

## 主なコマンド

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# スクリーニング実行
python scripts/screen_stocks.py --preset value --region japan

# 個別銘柄レポート
python scripts/stock_report.py --ticker 7203.T

# ポートフォリオ表示
python scripts/portfolio.py --action summary

# ストレステスト
python scripts/stress_test.py

# テスト実行
pytest tests/ -v
```

## Intent Routing

自然言語からスキルへの意図推論ルール（`.claude/rules/intent-routing.md`参照）。
「割安株を探して」→ `/screen-stocks`
「トヨタを分析して」→ `/stock-report`
「ポートフォリオを見せて」→ `/stock-portfolio`

## 重要ルール

1. 実装後は必ず`CLAUDE.md`のアーキテクチャ記述を更新する
2. 新スキル追加時は`.claude/skills/`にSKILL.mdを追加し、`intent-routing.md`を更新する
3. キャッシュは24時間有効。期限切れは自動的に再取得
4. 投資判断はユーザー自身の責任。本ツールは参考情報提供のみ

## 免責事項

本ソフトウェアは情報提供を目的としており、投資勧誘・投資助言ではありません。
投資判断および損益はすべてユーザーの責任です。
