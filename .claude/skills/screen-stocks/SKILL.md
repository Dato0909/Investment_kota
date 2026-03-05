# スキル: screen-stocks (割安株スクリーニング)

## 概要
Yahoo Finance APIを使って、15の投資戦略プリセットと60以上の地域から割安銘柄をスクリーニングします。

## トリガーパターン (自然言語)
以下のような意図を検出したときにこのスキルを実行してください:
- 「割安株を探して」「スクリーニングして」「バリュー株は？」
- 「高配当株を探して」「配当利回りが高い株は？」
- 「日本株でPER15倍以下の銘柄は？」
- 「米国株の成長株を探して」「GARP戦略で検索して」
- 「ディフェンシブ銘柄を探して」「景気敏感株は？」
- 「プリセット一覧を見せて」「どんな戦略がある？」
- 「対応地域を教えて」「どの国の株が買える？」

## 実行方法

### 基本スクリーニング
```bash
python scripts/screen_stocks.py --preset <プリセット名> --region <地域1> <地域2> --limit <件数>
```

### プリセット一覧表示
```bash
python scripts/screen_stocks.py --list-presets
```

### 地域一覧表示
```bash
python scripts/screen_stocks.py --list-regions
```

## プリセット一覧 (15戦略)

| プリセット名 | 説明 |
|------------|------|
| `value` | バリュー投資 (低PER・低PBR) |
| `deep_value` | ディープバリュー (極端な割安) |
| `quality_value` | クオリティバリュー (高ROE+割安) |
| `high_dividend` | 高配当 (利回り3%以上) |
| `income` | インカム (連続増配・安定) |
| `growth_value` | 成長割安 / GARP |
| `small_cap_value` | 小型バリュー |
| `defensive` | ディフェンシブ (低ベータ) |
| `turnaround` | ターンアラウンド (業績回復) |
| `momentum_value` | モメンタムバリュー |
| `sector_tech` | テクノロジー割安 |
| `sector_finance` | 金融セクター割安 |
| `sector_energy` | エネルギー割安 |
| `sector_healthcare` | ヘルスケア割安 |
| `global_value` | グローバルバリュー (60地域) |

## 主要地域コード

| コード | 地域 |
|-------|------|
| `japan` | 日本 (東証) |
| `us` | 米国 (NYSE/NASDAQ) |
| `hong_kong` | 香港 |
| `korea` | 韓国 |
| `taiwan` | 台湾 |
| `singapore` | シンガポール |
| `india_nse` | インド (NSE) |
| `uk` | 英国 |
| `germany` | ドイツ |
| `australia` | オーストラリア |

## 使用例

```bash
# 日本株のバリュー投資スクリーニング
python scripts/screen_stocks.py --preset value --region japan

# 米国株の高配当スクリーニング (上位30件)
python scripts/screen_stocks.py --preset high_dividend --region us --limit 30

# アジア全体の成長割安株
python scripts/screen_stocks.py --preset growth_value --region japan hong_kong korea taiwan singapore

# カスタムフィルタ (PER10以下・配当3%以上)
python scripts/screen_stocks.py --preset value --region japan --per-max 10 --div-min 3

# 詳細情報付きで表示
python scripts/screen_stocks.py --preset value --region japan --details
```

## 出力形式
Markdownテーブル形式で、スコア順に銘柄一覧を表示します。
各銘柄のPER・PBR・ROE・配当利回り・時価総額・セクターを表示。

## 注意事項
- データはYahoo Finance APIから取得 (24時間キャッシュ)
- サンプル銘柄ベースのスクリーニング (全上場銘柄は対象外)
- 投資判断はご自身でお願いします
