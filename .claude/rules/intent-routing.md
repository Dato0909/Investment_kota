# Intent Routing ルール

## 概要
ユーザーの自然言語入力から適切なスキルを自動選択するためのルールです。
Claude Codeはこのルールに従い、最適なスキルを実行してください。

## ルール優先順位

1. 明示的なキーワード → 最優先で対応スキルを選択
2. 文脈からの推論 → 会話の流れから意図を判断
3. 複合意図 → 複数スキルを順番に実行
4. 不明瞭な場合 → ユーザーに確認

---

## スキル判定ルール

### screen-stocks (割安株スクリーニング)
**トリガーキーワード:**
- スクリーニング、割安株、バリュー株、高配当株、低PER、低PBR
- 株を探して、銘柄を探して、銘柄を見つけて
- 日本株・米国株・アジア株 + 探して/見つけて
- プリセット一覧、戦略一覧、地域一覧

**実行パターン:**
```
「日本株でバリュー投資の銘柄を20件探して」
→ python scripts/screen_stocks.py --preset value --region japan --limit 20

「高配当の米国株を教えて」
→ python scripts/screen_stocks.py --preset high_dividend --region us

「プリセット一覧を見せて」
→ python scripts/screen_stocks.py --list-presets
```

---

### stock-report (個別銘柄レポート)
**トリガーキーワード:**
- 分析して、レポート、財務を見て、調べて
- PER、PBR、ROE、配当利回り (特定銘柄と組み合わせ)
- バリュートラップ？、投資してもいい？
- 比較して、どっちがいい？

**実行パターン:**
```
「トヨタを分析して」
→ python scripts/stock_report.py --ticker 7203.T

「AAPLとMSFTを比較して」
→ python scripts/stock_report.py --ticker AAPL MSFT

「この銘柄はバリュートラップ？ 7203.T」
→ python scripts/stock_report.py --ticker 7203.T
```

---

### watchlist (ウォッチリスト管理)
**トリガーキーワード:**
- ウォッチリスト、監視銘柄、気になる銘柄
- 追加して、登録して、削除して、外して
- ウォッチリストを見て、一覧

**実行パターン:**
```
「ウォッチリストを見せて」
→ python scripts/watchlist.py show

「7203.T をウォッチリストに追加して」
→ python scripts/watchlist.py add --ticker 7203.T

「7203.T をウォッチリストから削除」
→ python scripts/watchlist.py remove --ticker 7203.T
```

---

### stress-test (ストレステスト)
**トリガーキーワード:**
- ストレステスト、リスク分析、暴落、ショック
- リーマン、コロナ、金利上昇、円高
- 損失シミュレーション、最悪のケース

**実行パターン:**
```
「ポートフォリオのストレステストをして」
→ python scripts/stress_test.py

「暴落したらどうなる？」
→ python scripts/stress_test.py --scenarios market_crash

「金利上昇と円高のシナリオを見て」
→ python scripts/stress_test.py --scenarios rate_hike yen_appreciation
```

---

### stock-portfolio (ポートフォリオ管理)
**トリガーキーワード:**
- ポートフォリオ、保有銘柄、含み損益、損益
- 買った、売った、購入、売却、取引記録
- リバランス、均等配分
- 複利シミュレーション、積立、将来の資産
- HHI、集中度

**実行パターン:**
```
「ポートフォリオを見せて」
→ python scripts/portfolio.py summary

「7203.T を100株 2500円で買った」
→ python scripts/portfolio.py buy --ticker 7203.T --shares 100 --price 2500

「リバランスして均等にして」
→ python scripts/portfolio.py rebalance --equal

「100万円を年利7%で20年運用したら？」
→ python scripts/portfolio.py simulate --initial 1000000 --rate 7 --years 20
```

---

### investment-note (投資メモ)
**トリガーキーワード:**
- メモ、記録、ノート、テーゼ、懸念点
- 残して、記録して、書いて
- メモを見て、過去のメモ
- キーワードで検索

**実行パターン:**
```
「トヨタの投資テーゼをメモして」
→ python scripts/investment_note.py add --ticker 7203.T --title "投資テーゼ" --body "..."

「7203.T のメモを見せて」
→ python scripts/investment_note.py view --ticker 7203.T

「"配当" で検索して」
→ python scripts/investment_note.py search --keyword 配当
```

---

### graph-query (履歴検索)
**トリガーキーワード:**
- 過去に、以前に、履歴、分析した銘柄
- 横断検索、全体を見て
- どんな銘柄を、何を調べた

**実行パターン:**
```
「過去に分析した銘柄一覧は？」
→ python scripts/investment_note.py list
   + python scripts/watchlist.py show

「過去の取引を全部見せて」
→ python scripts/portfolio.py history
```

---

## 複合意図の処理

ユーザーが複数の意図を持つ場合、順番に実行します:

```
「トヨタを分析してウォッチリストに追加して」
→ 1. python scripts/stock_report.py --ticker 7203.T
   2. python scripts/watchlist.py add --ticker 7203.T --name "トヨタ自動車"

「日本の高配当株を探してトップ3のレポートを出して」
→ 1. python scripts/screen_stocks.py --preset high_dividend --region japan --limit 3
   2. python scripts/stock_report.py --ticker <結果の上位3銘柄>
```

## 意図が不明な場合

以下の場合はユーザーに確認してください:
1. ティッカーシンボルが不明確
2. 地域・プリセットが特定できない
3. 数値パラメータが不足している
