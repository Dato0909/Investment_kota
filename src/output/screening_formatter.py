"""
スクリーニング結果フォーマッタ
スクリーニング結果をMarkdownテーブルで出力します
"""

from __future__ import annotations

from typing import Any, Dict, List


def format_screening_results(result: Dict[str, Any], show_details: bool = False) -> str:
    """スクリーニング結果をMarkdown形式でフォーマット"""
    if "error" in result:
        return f"## エラー\n\n{result['error']}\n\n**利用可能なプリセット:** {', '.join(result.get('available_presets', []))}"

    preset_label = result.get("preset_label", result.get("preset_name", ""))
    preset_desc = result.get("preset_description", "")
    regions = result.get("regions", [])
    total_screened = result.get("total_screened", 0)
    total_filtered = result.get("total_filtered", 0)
    stocks = result.get("results", [])

    lines = [
        f"# スクリーニング結果: {preset_label}",
        f"",
        f"> {preset_desc}",
        f"",
        f"**対象地域:** {', '.join(regions)}  ",
        f"**スクリーニング:** {total_screened}銘柄中 {total_filtered}銘柄がフィルタ通過",
        f"**表示件数:** {len(stocks)}銘柄",
        f"",
    ]

    if not stocks:
        lines.append("条件に合致する銘柄が見つかりませんでした。フィルタ条件を緩和してください。")
        return "\n".join(lines)

    # メインテーブル
    lines.extend([
        "## 銘柄一覧",
        "",
        "| # | ティッカー | 銘柄名 | スコア | PER | PBR | ROE(%) | 配当(%) | 時価総額(B) | セクター |",
        "|---|-----------|-------|-------|-----|-----|--------|---------|------------|---------|",
    ])

    for i, s in enumerate(stocks, 1):
        ticker = s.get("ticker", "")
        name = _truncate(s.get("name", ticker), 15)
        score = f"{s.get('score', 0):.1f}"
        per = _fmt(s.get("per"), ".1f")
        pbr = _fmt(s.get("pbr"), ".2f")
        roe = _fmt(s.get("roe"), ".1f")
        dy = _fmt(s.get("dividend_yield"), ".2f")
        mc = _fmt(s.get("market_cap_billion"), ".1f")
        sector = _truncate(s.get("sector") or "-", 12)

        lines.append(
            f"| {i} | **{ticker}** | {name} | {score} | {per} | {pbr} | {roe} | {dy} | {mc} | {sector} |"
        )

    if show_details:
        lines.extend(["", "## 詳細データ", ""])
        for s in stocks:
            lines.extend(_format_stock_detail(s))

    lines.extend([
        "",
        "---",
        "*データソース: Yahoo Finance | キャッシュTTL: 24時間*",
        "*本結果は情報提供のみを目的としており、投資勧誘ではありません*",
    ])

    return "\n".join(lines)


def _format_stock_detail(stock: Dict[str, Any]) -> List[str]:
    """個別銘柄の詳細情報をフォーマット"""
    ticker = stock.get("ticker", "")
    name = stock.get("name", ticker)
    lines = [f"### {ticker} — {name}", ""]

    data = [
        ("セクター", stock.get("sector")),
        ("業種", stock.get("industry")),
        ("国/地域", stock.get("country")),
        ("現在株価", stock.get("current_price")),
        ("52週高値", stock.get("52w_high")),
        ("52週安値", stock.get("52w_low")),
        ("ベータ", stock.get("beta")),
        ("PER", stock.get("per")),
        ("PBR", stock.get("pbr")),
        ("PSR", stock.get("psr")),
        ("ROE(%)", stock.get("roe")),
        ("ROA(%)", stock.get("roa")),
        ("利益率(%)", stock.get("profit_margin")),
        ("配当利回り(%)", stock.get("dividend_yield")),
        ("配当性向(%)", stock.get("payout_ratio")),
        ("売上成長率(%)", stock.get("revenue_growth")),
        ("流動比率", stock.get("current_ratio")),
        ("D/E比率(%)", stock.get("debt_to_equity")),
    ]

    for label, val in data:
        if val is not None:
            if isinstance(val, float):
                lines.append(f"- **{label}**: {val:.2f}")
            else:
                lines.append(f"- **{label}**: {val}")

    lines.append("")
    return lines


def format_preset_list(presets: List[Dict[str, str]]) -> str:
    """プリセット一覧をフォーマット"""
    lines = [
        "# 利用可能なスクリーニングプリセット",
        "",
        "| プリセット名 | 表示名 | 説明 |",
        "|------------|-------|------|",
    ]
    for p in presets:
        lines.append(f"| `{p['name']}` | {p['label']} | {p['description']} |")
    return "\n".join(lines)


def format_region_list(regions: List[Dict[str, str]]) -> str:
    """地域一覧をフォーマット"""
    lines = [
        "# 利用可能な地域・取引所",
        "",
        "| 地域コード | 地域名 | 取引所 | 通貨 |",
        "|-----------|-------|-------|------|",
    ]
    for r in regions:
        lines.append(f"| `{r['name']}` | {r['label']} | {r['exchange']} | {r['currency']} |")
    return "\n".join(lines)


def _fmt(val: Any, fmt: str = ".2f") -> str:
    """数値フォーマット (Noneは "-" に変換)"""
    if val is None:
        return "-"
    try:
        return format(float(val), fmt)
    except (TypeError, ValueError):
        return str(val)


def _truncate(text: str, max_len: int) -> str:
    """文字列を指定長に切り詰める"""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"
