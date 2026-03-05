#!/usr/bin/env python3
"""
ストレステストスクリプト
Usage:
  python scripts/stress_test.py
  python scripts/stress_test.py --scenarios market_crash rate_hike
  python scripts/stress_test.py --list-scenarios
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.portfolio import Portfolio
from src.core.risk import RiskAnalyzer
from src.data.yahoo_client import YahooClient
from src.output.portfolio_formatter import format_stress_test


def main():
    parser = argparse.ArgumentParser(description="ポートフォリオストレステスト")
    parser.add_argument("--scenarios", nargs="+", default=None, help="実行するシナリオ名 (デフォルト: 全シナリオ)")
    parser.add_argument("--list-scenarios", action="store_true", help="利用可能なシナリオ一覧を表示")

    args = parser.parse_args()

    analyzer = RiskAnalyzer()

    if args.list_scenarios:
        scenarios = analyzer.list_scenarios()
        print("# 利用可能なストレステストシナリオ\n")
        print("| キー | シナリオ名 | 説明 | 市場ショック |")
        print("|-----|---------|------|-----------|")
        for s in scenarios:
            print(f"| `{s['key']}` | {s['name']} | {s['description']} | {s['market_shock_pct']:.0f}% |")
        return

    pf = Portfolio()
    holdings_map = pf.get_holdings()

    if not holdings_map:
        print("保有銘柄がありません。先にポートフォリオに銘柄を追加してください。")
        print("例: python scripts/portfolio.py buy --ticker 7203.T --shares 100 --price 2500")
        return

    tickers = list(holdings_map.keys())
    print(f"株価を取得中... ({', '.join(tickers)})")

    client = YahooClient()
    prices = {}
    for ticker in tickers:
        price = client.get_price(ticker)
        if price:
            prices[ticker] = price

    # セクター情報を含む保有銘柄リストを構築
    holdings_with_sector = []
    total_value = 0.0
    for ticker, h in holdings_map.items():
        current_price = prices.get(ticker, h.get("avg_cost", 0))
        market_value = h["total_shares"] * current_price
        total_value += market_value

        # セクター情報を取得
        sector = None
        try:
            info = client.get_info(ticker)
            if info:
                sector = info.get("sector")
        except Exception:
            pass

        holdings_with_sector.append({
            "ticker": ticker,
            "name": h.get("name", ticker),
            "market_value": market_value,
            "sector": sector,
            "beta": None,
        })

    print(f"\nポートフォリオ時価総額: {total_value:,.0f}")
    print("ストレステスト実行中...\n")

    result = analyzer.stress_test(
        holdings=holdings_with_sector,
        total_value=total_value,
        scenarios=args.scenarios,
    )

    print(format_stress_test(result))


if __name__ == "__main__":
    main()
