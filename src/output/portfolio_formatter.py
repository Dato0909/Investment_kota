"""
ポートフォリオ出力フォーマッタ
ポートフォリオサマリー・損益・ストレステスト結果をMarkdownで出力します
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def format_portfolio_summary(summary: Dict[str, Any]) -> str:
    """ポートフォリオサマリーをMarkdown形式でフォーマット"""
    total_mv = summary.get("total_market_value", 0)
    total_cost = summary.get("total_cost_basis", 0)
    total_pnl = summary.get("total_unrealized_pnl", 0)
    total_return = summary.get("total_return_pct", 0)
    hhi = summary.get("hhi", 0)
    hhi_risk = summary.get("hhi_risk", "-")
    holdings_count = summary.get("holdings_count", 0)

    pnl_sign = "+" if total_pnl >= 0 else ""
    return_sign = "+" if total_return >= 0 else ""

    lines = [
        "# ポートフォリオサマリー",
        "",
        "## 総資産状況",
        "",
        f"| 項目 | 金額 |",
        f"|-----|-----|",
        f"| 時価総額合計 | {total_mv:,.0f} |",
        f"| 取得コスト合計 | {total_cost:,.0f} |",
        f"| 含み損益 | {pnl_sign}{total_pnl:,.0f} ({return_sign}{total_return:.2f}%) |",
        f"| 保有銘柄数 | {holdings_count}銘柄 |",
        f"| HHI集中度指数 | {hhi:.4f} ({hhi_risk}) |",
        "",
        "## 銘柄別損益",
        "",
        "| ティッカー | 銘柄名 | 株数 | 平均取得価格 | 現在値 | 時価 | 含み損益 | 損益率 | 比率 |",
        "|-----------|-------|------|------------|------|-----|---------|-------|-----|",
    ]

    allocation = summary.get("allocation", [])
    holdings = {h["ticker"]: h for h in summary.get("holdings", [])}

    for a in allocation:
        ticker = a["ticker"]
        name = _truncate(a.get("name", ticker), 12)
        weight = a.get("weight_pct", 0)
        mv = a.get("market_value") or 0
        h = holdings.get(ticker, {})
        shares = h.get("total_shares", 0)
        avg_cost = h.get("avg_cost", 0)
        current = h.get("current_price") or 0
        pnl = h.get("unrealized_pnl") or 0
        pnl_pct = h.get("unrealized_pnl_pct") or 0
        pnl_str = f"{'+' if pnl >= 0 else ''}{pnl:,.0f} ({'+' if pnl_pct >= 0 else ''}{pnl_pct:.2f}%)"

        lines.append(
            f"| **{ticker}** | {name} | {shares:,.1f} | {avg_cost:,.2f} | "
            f"{current:,.2f} | {mv:,.0f} | {pnl_str} | {weight:.1f}% |"
        )

    lines.extend(["", "---", "*含み損益は未実現損益です。確定申告対象は実現損益を確認してください*"])
    return "\n".join(lines)


def format_stress_test(stress_result: Dict[str, Any]) -> str:
    """ストレステスト結果をMarkdown形式でフォーマット"""
    total_value = stress_result.get("total_value", 0)
    scenarios = stress_result.get("scenarios", {})
    worst_key = stress_result.get("worst_scenario")
    best_key = stress_result.get("best_scenario")

    lines = [
        "# ストレステスト結果",
        "",
        f"**ポートフォリオ時価総額:** {total_value:,.0f}",
        "",
        "## シナリオ別影響サマリー",
        "",
        "| シナリオ | 推定損失 | 損失率 | ショック後資産 |",
        "|---------|---------|-------|-------------|",
    ]

    # ダメージ降順でソート
    sorted_scenarios = sorted(
        scenarios.items(),
        key=lambda kv: kv[1].get("portfolio_change_pct", 0)
    )

    for key, data in sorted_scenarios:
        name = data.get("name", key)
        change = data.get("portfolio_change", 0)
        change_pct = data.get("portfolio_change_pct", 0)
        post_shock = data.get("post_shock_value", 0)
        marker = " ⚠️ 最悪" if key == worst_key else (" ✅ 最良" if key == best_key else "")
        lines.append(
            f"| {name}{marker} | {change:,.0f} | {change_pct:.2f}% | {post_shock:,.0f} |"
        )

    # 最悪シナリオの詳細
    if worst_key and worst_key in scenarios:
        worst = scenarios[worst_key]
        lines.extend([
            "",
            f"## 最悪シナリオ詳細: {worst.get('name', worst_key)}",
            "",
            f"> {worst.get('description', '')}",
            "",
            "| ティッカー | セクター | 現在時価 | 推定損失 | 損失率 | ショック後 |",
            "|-----------|---------|--------|---------|-------|---------|",
        ])
        for h in worst.get("holding_impacts", [])[:10]:
            ticker = h.get("ticker", "")
            sector = _truncate(h.get("sector") or "-", 12)
            mv = h.get("market_value", 0)
            loss = h.get("estimated_loss", 0)
            shock_pct = h.get("effective_shock_pct", 0)
            post = h.get("post_shock_value", 0)
            lines.append(
                f"| **{ticker}** | {sector} | {mv:,.0f} | {loss:,.0f} | {shock_pct:.1f}% | {post:,.0f} |"
            )

    lines.extend([
        "",
        "---",
        "*ストレステストは過去データと仮定に基づく試算です。実際の損失を保証するものではありません*",
    ])
    return "\n".join(lines)


def format_rebalance(suggestions: List[Dict[str, Any]], total_value: float) -> str:
    """リバランス提案をMarkdown形式でフォーマット"""
    lines = [
        "# リバランス提案",
        "",
        f"**ポートフォリオ時価総額:** {total_value:,.0f}",
        "",
        "| ティッカー | 現在比率 | 目標比率 | 差分 | 売買金額 | アクション |",
        "|-----------|---------|--------|-----|--------|---------|",
    ]

    for s in suggestions:
        ticker = s.get("ticker", "")
        current_w = s.get("current_weight_pct", 0)
        target_w = s.get("target_weight_pct", 0)
        diff_w = target_w - current_w
        diff_val = s.get("diff_value", 0)
        action = s.get("action", "hold")
        action_emoji = {"buy": "📈 買い増し", "sell": "📉 売却", "hold": "⏸ 維持"}.get(action, action)
        lines.append(
            f"| **{ticker}** | {current_w:.1f}% | {target_w:.1f}% | "
            f"{'+' if diff_w >= 0 else ''}{diff_w:.1f}% | "
            f"{'+' if diff_val >= 0 else ''}{diff_val:,.0f} | {action_emoji} |"
        )

    lines.extend(["", "---", "*リバランスは手数料・税金を考慮の上、ご判断ください*"])
    return "\n".join(lines)


def format_compound_simulation(results: List[Dict[str, Any]], params: Dict[str, Any]) -> str:
    """複利シミュレーション結果をMarkdown形式でフォーマット"""
    init = params.get("initial_investment", 0)
    rate = params.get("annual_return_pct", 0)
    div = params.get("annual_dividend_pct", 0)
    monthly = params.get("monthly_contribution", 0)
    years = params.get("years", 0)

    lines = [
        "# 複利シミュレーション",
        "",
        "## 設定条件",
        f"- 初期投資額: {init:,.0f}",
        f"- 年間リターン: {rate:.1f}%",
        f"- 配当利回り: {div:.1f}%",
        f"- 毎月積立: {monthly:,.0f}",
        f"- シミュレーション期間: {years}年",
        "",
        "## 年次推移",
        "",
        "| 年 | 資産総額 | 投資累計 | 含み利益 | 年間配当 | リターン率 |",
        "|----|--------|--------|--------|--------|---------|",
    ]

    milestone_years = {1, 3, 5, 10, 15, 20, 25, 30}
    for r in results:
        year = r.get("year", 0)
        if year not in milestone_years and year != years:
            continue
        pv = r.get("portfolio_value", 0)
        ti = r.get("total_invested", 0)
        gain = r.get("total_gain", 0)
        div_a = r.get("dividend_received_annual", 0)
        ret_pct = r.get("return_pct", 0)
        lines.append(
            f"| {year}年 | {pv:,.0f} | {ti:,.0f} | "
            f"{'+' if gain >= 0 else ''}{gain:,.0f} | {div_a:,.0f} | {ret_pct:.1f}% |"
        )

    if results:
        final = results[-1]
        final_pv = final.get("portfolio_value", 0)
        final_ti = final.get("total_invested", 0)
        final_gain = final.get("total_gain", 0)
        lines.extend([
            "",
            f"**{years}年後の資産総額: {final_pv:,.0f}**  ",
            f"投資元本合計: {final_ti:,.0f}  ",
            f"運用利益合計: {'+' if final_gain >= 0 else ''}{final_gain:,.0f}  ",
            f"倍率: {final_pv / init:.2f}倍" if init > 0 else "",
        ])

    lines.extend(["", "---", "*シミュレーションは一定リターンを仮定した試算です*"])
    return "\n".join(lines)


def format_watchlist(records: List[Dict[str, str]], current_prices: Optional[Dict[str, float]] = None) -> str:
    """ウォッチリストをMarkdown形式でフォーマット"""
    if not records:
        return "# ウォッチリスト\n\nウォッチリストは空です。`/watchlist add [ティッカー]` で銘柄を追加してください。"

    lines = [
        "# ウォッチリスト",
        "",
        f"登録銘柄数: {len(records)}",
        "",
        "| ティッカー | 銘柄名 | 追加日 | 目標価格 | 現在価格 | メモ |",
        "|-----------|-------|-------|--------|--------|-----|",
    ]

    for r in records:
        ticker = r.get("ticker", "")
        name = _truncate(r.get("name", ticker), 12)
        added = r.get("added_date", "-")
        target = r.get("target_price", "-") or "-"
        note = _truncate(r.get("note", ""), 20)
        current = "-"
        if current_prices and ticker in current_prices:
            current = f"{current_prices[ticker]:,.2f}"
        lines.append(f"| **{ticker}** | {name} | {added} | {target} | {current} | {note} |")

    return "\n".join(lines)


def _truncate(text: str, max_len: int) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len - 1] + "…"
