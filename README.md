# Investment_kota — 割安株スクリーニング・ポートフォリオ管理システム

Claude Code Skills として動作する投資分析ツールです。
Yahoo Finance API を使用して、60以上の地域から割安銘柄をスクリーニングし、ポートフォリオ管理・リスク分析を行います。

## 特徴

- **自然言語ファースト**: 日本語で話しかけるだけで、適切なスキルが自動実行
- **8つのスキル**: スクリーニング〜ポートフォリオ管理まで投資ワークフロー全体をカバー
- **15の投資戦略プリセット**: バリュー・高配当・成長・セクター別など
- **60地域対応**: 日本・米国・アジア・欧州・中南米など
- **24時間キャッシュ**: Yahoo Finance APIの結果をローカルにキャッシュ
- **永続化**: CSV・Markdownでデータを保存。セッションをまたいで参照可能

## セットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定 (オプション)
cp .env.example .env
```

**必須:** Python 3.10以上

## 8つのスキル

### 1. `/screen-stocks` — 割安株スクリーニング
```bash
python scripts/screen_stocks.py --preset value --region japan us
python scripts/screen_stocks.py --list-presets   # プリセット一覧
python scripts/screen_stocks.py --list-regions   # 地域一覧
```

### 2. `/stock-report` — 個別銘柄レポート
```bash
python scripts/stock_report.py --ticker 7203.T
python scripts/stock_report.py --ticker AAPL MSFT GOOGL  # 比較
```

### 3. `/watchlist` — ウォッチリスト管理
```bash
python scripts/watchlist.py show
python scripts/watchlist.py add --ticker 7203.T --target 3000
python scripts/watchlist.py remove --ticker 7203.T
```

### 4. `/stress-test` — ストレステスト (8シナリオ)
```bash
python scripts/stress_test.py
python scripts/stress_test.py --scenarios market_crash rate_hike
```

### 5. `/stock-portfolio` — ポートフォリオ管理
```bash
python scripts/portfolio.py summary
python scripts/portfolio.py buy --ticker 7203.T --shares 100 --price 2500
python scripts/portfolio.py sell --ticker 7203.T --shares 50 --price 2800
python scripts/portfolio.py rebalance --equal
python scripts/portfolio.py simulate --initial 1000000 --rate 7 --years 20
```

### 6. `/investment-note` — 投資メモ
```bash
python scripts/investment_note.py add --ticker 7203.T --title "投資テーゼ" --body "..."
python scripts/investment_note.py view --ticker 7203.T
python scripts/investment_note.py search --keyword 配当
```

### 7. `/market-research` — マーケット調査
```bash
# セクター別スクリーニング
python scripts/screen_stocks.py --preset sector_tech --region us japan
```

### 8. `/graph-query` — 履歴横断検索
```bash
python scripts/investment_note.py list
python scripts/portfolio.py history
```

## 15の投資戦略プリセット

| プリセット | 説明 |
|----------|------|
| `value` | バリュー投資 (低PER・低PBR) |
| `deep_value` | ディープバリュー |
| `quality_value` | クオリティバリュー (高ROE+割安) |
| `high_dividend` | 高配当 (3%以上) |
| `income` | インカム (連続増配) |
| `growth_value` | 成長割安 / GARP |
| `small_cap_value` | 小型バリュー (時価総額300億以下) |
| `defensive` | ディフェンシブ (低ベータ) |
| `turnaround` | ターンアラウンド |
| `momentum_value` | モメンタムバリュー |
| `sector_tech` | テクノロジー割安 |
| `sector_finance` | 金融セクター割安 |
| `sector_energy` | エネルギー割安 |
| `sector_healthcare` | ヘルスケア割安 |
| `global_value` | グローバルバリュー (60地域) |

## ストレステストシナリオ (8シナリオ)

| シナリオ | 市場ショック |
|---------|-----------|
| 市場暴落 (リーマン級) | -40% |
| 急激な金利上昇 | -20% |
| 急激な円高 | -15% |
| インフレ急騰 | -18% |
| 地政学リスク | -20% |
| テックバブル崩壊 | -25% |
| 新型パンデミック | -30% |
| 軽度な景気後退 | -15% |

## アーキテクチャ

```
Investment_kota/
├── .claude/
│   ├── skills/      # 8つのClaude Code Skills (SKILL.md)
│   └── rules/       # intent-routing.md (自然言語→スキル変換ルール)
├── config/
│   ├── screening_presets.yaml   # 15投資戦略プリセット
│   └── exchanges.yaml           # 60+地域取引所
├── src/
│   ├── core/        # ビジネスロジック (screening/portfolio/risk/research)
│   ├── data/        # データ層 (yahoo_client/cache)
│   └── output/      # フォーマッタ (screening/portfolio/report)
├── scripts/         # CLI実行スクリプト
├── data/            # 永続化データ (portfolio.csv/watchlist.csv/notes/)
└── tests/           # テストスイート (102テスト)
```

## テスト

```bash
pytest tests/ -v
# 102テスト、約1.5秒で完了
```

## データ保存

| データ | 場所 | 形式 |
|-------|------|------|
| ポートフォリオ | `data/portfolio.csv` | CSV |
| ウォッチリスト | `data/watchlist.csv` | CSV |
| 投資メモ | `data/notes/*.md` | Markdown |
| APIキャッシュ | `data/cache/*.json` | JSON (24h TTL) |
| スクリーニング設定 | `config/screening_presets.yaml` | YAML |
| 取引所定義 | `config/exchanges.yaml` | YAML |

## 免責事項

本ソフトウェアは情報提供を目的としており、投資勧誘・投資助言ではありません。
投資判断および損益はすべてユーザーの責任です。
金融商品取引法上の投資助言業には該当しません (個人利用のみ)。