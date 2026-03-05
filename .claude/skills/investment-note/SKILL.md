# スキル: investment-note (投資メモ管理)

## 概要
銘柄ごとの投資テーゼ・懸念点・分析メモをMarkdown形式で保存・管理します。
セッションをまたいで過去の分析記録を参照できます。

## トリガーパターン (自然言語)
以下のような意図を検出したときにこのスキルを実行してください:
- 「○○についてメモを残して」「投資テーゼを記録して」
- 「懸念点をまとめて」「リスクをメモして」
- 「○○のメモを見せて」「過去の分析は？」
- 「メモ一覧を見せて」「どの銘柄にメモがある？」
- 「配当に関するメモを検索」「キーワードで検索」

## 実行方法

### メモ一覧表示
```bash
python scripts/investment_note.py list
```

### メモ追加
```bash
python scripts/investment_note.py add --ticker <ティッカー> --title <タイトル> --body <本文> [--tags <タグ1> <タグ2>]
```

### メモ表示
```bash
python scripts/investment_note.py view --ticker <ティッカー>
```

### キーワード検索
```bash
python scripts/investment_note.py search --keyword <キーワード>
```

## 使用例

```bash
# トヨタの投資テーゼを記録
python scripts/investment_note.py add \
  --ticker 7203.T \
  --title "投資テーゼ" \
  --body "EV移行期のリスクはあるが、HV技術の優位性と低PBRが魅力。配当3%台も評価。" \
  --tags バリュー 配当 自動車

# ソニーのリスクをメモ
python scripts/investment_note.py add \
  --ticker 6758.T \
  --title "リスク" \
  --body "ゲーム部門の成長鈍化が懸念。半導体・エンタメの多角化は強み。" \
  --tags エンタメ 半導体

# トヨタのメモを表示
python scripts/investment_note.py view --ticker 7203.T

# 「配当」を含むメモを検索
python scripts/investment_note.py search --keyword 配当

# 全メモ一覧
python scripts/investment_note.py list
```

## データ保存先
`data/notes/<ティッカー>.md` (Markdown形式)
