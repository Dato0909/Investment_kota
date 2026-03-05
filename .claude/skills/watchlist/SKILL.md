# スキル: watchlist (ウォッチリスト管理)

## 概要
気になる銘柄をウォッチリストに登録・管理します。
CSV形式で永続保存され、次のセッションでも参照できます。

## トリガーパターン (自然言語)
以下のような意図を検出したときにこのスキルを実行してください:
- 「ウォッチリストを見せて」「監視銘柄一覧を表示」
- 「○○をウォッチリストに追加して」「気になる銘柄に登録」
- 「ウォッチリストから○○を削除して」「外して」
- 「ウォッチリストの現在値を確認」

## 実行方法

### 一覧表示
```bash
python scripts/watchlist.py show
python scripts/watchlist.py show --no-price  # 株価取得なし (高速)
```

### 銘柄追加
```bash
python scripts/watchlist.py add --ticker <ティッカー> [--name <銘柄名>] [--target <目標価格>] [--note <メモ>]
```

### 銘柄削除
```bash
python scripts/watchlist.py remove --ticker <ティッカー>
```

## 使用例

```bash
# ウォッチリストを表示 (現在価格付き)
python scripts/watchlist.py show

# トヨタを目標価格付きで追加
python scripts/watchlist.py add --ticker 7203.T --name "トヨタ自動車" --target 3000 --note "配当利回り注目"

# アップルを追加
python scripts/watchlist.py add --ticker AAPL --note "AI関連で注目"

# 銘柄を削除
python scripts/watchlist.py remove --ticker 7203.T
```

## データ保存先
`data/watchlist.csv`
