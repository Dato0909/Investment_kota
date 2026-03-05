# スキル: graph-query (分析履歴横断検索)

## 概要
過去の分析履歴・投資メモ・ウォッチリスト・ポートフォリオ記録を横断的に検索します。
「先週分析した銘柄」「配当に関するメモ」「損益が高い銘柄」などを素早く参照できます。

## トリガーパターン (自然言語)
以下のような意図を検出したときにこのスキルを実行してください:
- 「過去に分析した銘柄は？」「今まで見た株は？」
- 「配当に関するメモを探して」「バリュートラップのメモは？」
- 「どんな銘柄をウォッチしてた？」「ウォッチリストの履歴は？」
- 「損益がプラスの銘柄は？」「含み益が大きいのは？」
- 「過去の取引履歴を検索」「○○円以上で買った銘柄は？」

## 実行方法

### 投資メモ検索
```bash
# キーワードでメモを検索
python scripts/investment_note.py search --keyword <キーワード>

# 全メモ一覧
python scripts/investment_note.py list
```

### ウォッチリスト確認
```bash
python scripts/watchlist.py show
```

### ポートフォリオ・取引履歴検索
```bash
# 売買履歴確認
python scripts/portfolio.py history

# ポートフォリオサマリー
python scripts/portfolio.py summary
```

## 検索例

```bash
# 「高配当」に関するメモを検索
python scripts/investment_note.py search --keyword 高配当

# 「バリュートラップ」に関するメモ
python scripts/investment_note.py search --keyword バリュートラップ

# ウォッチリストの全銘柄を現在価格付きで表示
python scripts/watchlist.py show

# 全売買履歴を確認
python scripts/portfolio.py history
```

## データソース
- 投資メモ: `data/notes/*.md`
- ウォッチリスト: `data/watchlist.csv`
- ポートフォリオ: `data/portfolio.csv`
- APIキャッシュ: `data/cache/*.json`
