"""
個別銘柄レポートフォーマッタ
詳細財務分析レポートをMarkdown形式で出力します
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def format_stock_report(analysis: Dict[str, Any]) -> str:
    """個別銘柄の詳細分析レポートをMarkdown形式でフォーマット"""
    if "error" in analysis:
        return f"## エラー\n\n{analysis['error']}"

    ticker = analysis.get("ticker", "")
    metrics = analysis.get("metrics", {})
    valuation = analysis.get("valuation", {})
    health = analysis.get("health", {})
    value_trap = analysis.get("value_trap", {})
    summary = analysis.get("summary", {})

    name = metrics.get("name", ticker)
    sector = metrics.get("sector", "-")
    industry = metrics.get("industry", "-")
    country = metrics.get("country", "-")
    currency = metrics.get("currency", "")

    # サマリーヘッダー
    lines = [
        f"# {ticker} — {name}",
        f"",
        f"**セクター:** {sector} | **業種:** {industry} | **国:** {country}",
        f"",
    ]

    # 総合評価バナー
    total_score = summary.get("total_score")
    recommendation = summary.get("recommendation", "-")
    trap_risk = value_trap.get("risk_level", "MEDIUM")
    trap_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW_MEDIUM": "🟡", "LOW": "🟢"}.get(trap_risk, "🟡")

    score_bar = _score_bar(total_score)
    lines.extend([
        "## 総合評価",
        "",
        f"| 項目 | 評価 |",
        f"|-----|-----|",
        f"| 投資推奨 | **{recommendation}** |",
        f"| 総合スコア | {total_score:.0f}/100 {score_bar}" if total_score else "| 総合スコア | N/A |",
        f"| バリュエーション | {valuation.get('overall_rating', 'N/A')} ({valuation.get('overall_score', 'N/A')}) |",
        f"| 財務健全性 | {health.get('overall_rating', 'N/A')} ({health.get('overall_score', 'N/A')}) |",
        f"| バリュートラップリスク | {trap_emoji} {value_trap.get('verdict', '-')} |",
        "",
    ])

    # 株価情報
    current_price = metrics.get("current_price")
    high_52w = metrics.get("52w_high")
    low_52w = metrics.get("52w_low")
    beta = metrics.get("beta")

    if current_price:
        lines.extend([
            "## 株価情報",
            "",
            f"| 項目 | 値 |",
            f"|-----|---|",
            f"| 現在株価 | {current_price:,.2f} {currency} |",
        ])
        if high_52w:
            lines.append(f"| 52週高値 | {high_52w:,.2f} {currency} |")
        if low_52w:
            lines.append(f"| 52週安値 | {low_52w:,.2f} {currency} |")
        if high_52w and low_52w and high_52w > low_52w:
            position_pct = (current_price - low_52w) / (high_52w - low_52w) * 100
            lines.append(f"| 52週レンジ内位置 | {position_pct:.0f}% (高値={high_52w:,.2f}, 安値={low_52w:,.2f}) |")
        if beta:
            lines.append(f"| ベータ | {beta:.2f} |")
        mc = metrics.get("market_cap_billion")
        if mc:
            lines.append(f"| 時価総額 | {mc:.1f}B {currency} |")
        lines.append("")

    # バリュエーション指標
    lines.extend([
        "## バリュエーション指標",
        "",
        "| 指標 | 値 | 評価 | コメント |",
        "|-----|---|-----|-------|",
    ])

    val_per = valuation.get("per", {})
    val_pbr = valuation.get("pbr", {})

    def _vrow(label: str, data: Dict) -> str:
        val = data.get("value")
        rating = data.get("rating", "-")
        comment = data.get("comment", "")
        val_str = f"{val:.2f}" if val is not None else "N/A"
        return f"| {label} | {val_str} | {rating} | {comment} |"

    lines.extend([
        _vrow("PER (株価収益率)", val_per),
        _vrow("PBR (株価純資産倍率)", val_pbr),
    ])

    psr = valuation.get("psr", {}).get("value")
    ev_ebitda = valuation.get("ev_ebitda", {}).get("value")
    div_yield = valuation.get("dividend_yield", {})

    if psr:
        lines.append(f"| PSR (株価売上高倍率) | {psr:.2f} | - | - |")
    if ev_ebitda:
        lines.append(f"| EV/EBITDA | {ev_ebitda:.2f} | - | - |")
    lines.append(_vrow("配当利回り", div_yield))

    payout = metrics.get("payout_ratio")
    if payout:
        lines.append(f"| 配当性向 | {payout:.1f}% | - | - |")

    lines.append("")

    # 収益性指標
    prof = health.get("profitability", {})
    lines.extend([
        "## 収益性指標",
        "",
        f"**総合評価:** {prof.get('rating', 'N/A')} (スコア: {prof.get('score', 'N/A')})",
        "",
        "| 指標 | 値 |",
        "|-----|---|",
    ])
    for label, key in [
        ("ROE (自己資本利益率)", "roe"),
        ("ROA (総資産利益率)", "roa"),
        ("純利益率", "profit_margin"),
        ("営業利益率", "operating_margin"),
        ("粗利益率", "gross_margin"),
    ]:
        val = prof.get(key) or metrics.get(key)
        if val is not None:
            lines.append(f"| {label} | {val:.2f}% |")
    lines.append("")

    # 財務健全性
    safety = health.get("safety", {})
    growth_data = health.get("growth", {})
    lines.extend([
        "## 財務健全性",
        "",
        f"**総合評価:** {safety.get('rating', 'N/A')} (スコア: {safety.get('score', 'N/A')})",
        "",
        "| 指標 | 値 |",
        "|-----|---|",
    ])
    for label, key in [
        ("流動比率", "current_ratio"),
        ("当座比率", "quick_ratio"),
        ("D/E比率(%)", "debt_to_equity"),
    ]:
        val = safety.get(key) or metrics.get(key)
        if val is not None:
            lines.append(f"| {label} | {val:.2f} |")
    lines.append("")

    # 成長性
    lines.extend([
        "## 成長性",
        "",
        f"**総合評価:** {growth_data.get('rating', 'N/A')} (スコア: {growth_data.get('score', 'N/A')})",
        "",
        "| 指標 | 値 |",
        "|-----|---|",
    ])
    for label, key in [
        ("売上成長率", "revenue_growth"),
        ("利益成長率", "earnings_growth"),
    ]:
        val = growth_data.get(key) or metrics.get(key)
        if val is not None:
            lines.append(f"| {label} | {'+' if val >= 0 else ''}{val:.1f}% |")
    lines.append("")

    # バリュートラップ診断
    lines.extend([
        "## バリュートラップ診断",
        "",
        f"**リスクレベル:** {trap_emoji} {trap_risk}",
        f"**判定:** {value_trap.get('verdict', '-')}",
        "",
    ])

    red_flags = value_trap.get("red_flags", [])
    warnings = value_trap.get("warnings", [])

    if red_flags:
        lines.extend(["### レッドフラグ", ""])
        for flag in red_flags:
            lines.append(f"- 🔴 {flag}")
        lines.append("")

    if warnings:
        lines.extend(["### 注意点", ""])
        for w in warnings:
            lines.append(f"- 🟡 {w}")
        lines.append("")

    if not red_flags and not warnings:
        lines.extend(["🟢 主要なリスク要因は検出されませんでした", ""])

    lines.extend([
        "---",
        f"*データソース: Yahoo Finance | 分析日: {_today()}*",
        "*本レポートは情報提供のみを目的としており、投資勧誘・投資助言ではありません*",
        "*最終的な投資判断はご自身の責任で行ってください*",
    ])

    return "\n".join(lines)


def format_comparison(comparisons: List[Dict[str, Any]]) -> str:
    """複数銘柄の比較表をフォーマット"""
    lines = [
        "# 銘柄比較",
        "",
        "| ランク | ティッカー | 銘柄名 | スコア | バリュエーション | 財務健全性 | トラップリスク | 投資推奨 |",
        "|------|-----------|-------|------|--------------|----------|-------------|--------|",
    ]

    for i, c in enumerate(comparisons, 1):
        ticker = c.get("ticker", "")
        name = _truncate(c.get("name", ticker), 12)
        total_score = c.get("total_score")
        val_score = c.get("valuation_score")
        health_score = c.get("health_score")
        trap_risk = c.get("trap_risk", "-")
        recommendation = _truncate(c.get("recommendation", "-"), 15)
        trap_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW_MEDIUM": "🟡", "LOW": "🟢"}.get(trap_risk, "🟡")

        lines.append(
            f"| {i} | **{ticker}** | {name} | "
            f"{total_score:.0f}" if total_score else f"| {i} | **{ticker}** | {name} | N/A"
            f" | {val_score:.0f}" if val_score else " | N/A"
            f" | {health_score:.0f}" if health_score else " | N/A"
            f" | {trap_emoji} {trap_risk} | {recommendation} |"
        )

    return "\n".join(lines)


def _score_bar(score: Optional[float], width: int = 10) -> str:
    """スコアをテキストバーで表現"""
    if score is None:
        return ""
    filled = int(score / 100 * width)
    return f"[{'█' * filled}{'░' * (width - filled)}]"


def _truncate(text: str, max_len: int) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len - 1] + "…"


def _today() -> str:
    from datetime import date
    return str(date.today())
