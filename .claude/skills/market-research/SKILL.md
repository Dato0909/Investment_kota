# スキル: market-research (マーケット調査)

## 概要
銘柄・業界・マーケットの深掘り調査を行います。
複数銘柄のスクリーニング指標を一括取得し、セクター別・地域別の概況を分析します。

## トリガーパターン (自然言語)
以下のような意図を検出したときにこのスキルを実行してください:
- 「半導体セクターの概況は？」「EV関連株は？」
- 「日本の自動車メーカーを比べて」「銀行株の状況は？」
- 「今の市場環境は？」「景気はどう？」
- 「○○業界の銘柄を調べて」
- 「テック株・配当株・グロース株の比較」

## 実行方法

複数銘柄を一括レポート生成:
```bash
python scripts/stock_report.py --ticker <ティッカー1> <ティッカー2> <ティッカー3>
```

セクター内の銘柄をスクリーニングで絞り込み:
```bash
python scripts/screen_stocks.py --preset sector_tech --region us
python scripts/screen_stocks.py --preset sector_finance --region japan
python scripts/screen_stocks.py --preset sector_energy --region us uk
```

## セクター別スクリーニング例

### テクノロジーセクター
```bash
python scripts/screen_stocks.py --preset sector_tech --region us japan
```

### 金融セクター
```bash
python scripts/screen_stocks.py --preset sector_finance --region japan us hong_kong
```

### エネルギーセクター
```bash
python scripts/screen_stocks.py --preset sector_energy --region us uk norway
```

### ヘルスケアセクター
```bash
python scripts/screen_stocks.py --preset sector_healthcare --region us uk germany
```

## 銘柄群の比較調査例

### 日本自動車メーカー
```bash
python scripts/stock_report.py --ticker 7203.T 7267.T 7270.T
```

### 日本メガバンク
```bash
python scripts/stock_report.py --ticker 8306.T 8316.T 8411.T
```

### 米国ビッグテック (GAFAM + N)
```bash
python scripts/stock_report.py --ticker AAPL MSFT GOOGL AMZN META NVDA
```

### 半導体関連
```bash
python scripts/stock_report.py --ticker NVDA ASML.AS 2330.TW 005930.KS
```
