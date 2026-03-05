# スキル: stock-portfolio (ポートフォリオ管理)

## 概要
株式の売買記録を管理し、損益計算・HHI集中度分析・リバランス提案・複利シミュレーションを提供します。

## トリガーパターン (自然言語)
以下のような意図を検出したときにこのスキルを実行してください:
- 「ポートフォリオを見せて」「保有銘柄の損益は？」「含み益はいくら？」
- 「○○を○株 ○○円で買った」「買い記録を追加して」
- 「○○を売った」「売り記録を追加」
- 「売買履歴を見せて」「取引履歴」
- 「リバランスして」「均等配分にして」
- 「HHI集中度は？」「分散できてる？」
- 「複利シミュレーション」「20年後の資産を計算して」「100万円を年利7%で運用したら？」

## 実行方法

### ポートフォリオサマリー表示
```bash
python scripts/portfolio.py summary
```

### 買い記録の追加
```bash
python scripts/portfolio.py buy --ticker <ティッカー> --shares <株数> --price <価格> [--commission <手数料>] [--date YYYY-MM-DD] [--note <メモ>]
```

### 売り記録の追加
```bash
python scripts/portfolio.py sell --ticker <ティッカー> --shares <株数> --price <価格>
```

### 売買履歴の表示
```bash
python scripts/portfolio.py history
```

### リバランス提案
```bash
python scripts/portfolio.py rebalance --equal  # 均等ウェイト
```

### 複利シミュレーション
```bash
python scripts/portfolio.py simulate --initial <初期投資額> --rate <年利%> --years <年数> [--dividend <配当利回り%>] [--monthly <毎月積立額>]
```

## 使用例

```bash
# ポートフォリオ確認
python scripts/portfolio.py summary

# トヨタ100株を2500円で購入
python scripts/portfolio.py buy --ticker 7203.T --shares 100 --price 2500 --commission 500

# ソニー50株を売却
python scripts/portfolio.py sell --ticker 6758.T --shares 50 --price 12000

# 売買履歴確認
python scripts/portfolio.py history

# 均等ウェイトにリバランス
python scripts/portfolio.py rebalance --equal

# 100万円を年利7%・20年間の複利シミュレーション
python scripts/portfolio.py simulate --initial 1000000 --rate 7 --years 20

# 毎月3万円積立・年利5%・30年
python scripts/portfolio.py simulate --initial 500000 --rate 5 --years 30 --monthly 30000
```

## HHI集中度指数の目安

| HHI値 | リスク評価 |
|-------|---------|
| < 0.10 | 低リスク (十分に分散) |
| 0.10-0.18 | 中リスク (やや集中) |
| 0.18-0.25 | 高リスク (集中傾向) |
| > 0.25 | 非常に高いリスク |

## データ保存先
`data/portfolio.csv`
