#!/usr/bin/env python3
"""
ポートフォリオ管理スクリプト
Usage:
  python scripts/portfolio.py summary
  python scripts/portfolio.py buy --ticker 7203.T --shares 100 --price 2500
  python scripts/portfolio.py sell --ticker 7203.T --shares 50 --price 2800
  python scripts/portfolio.py history
  python scripts/portfolio.py rebalance --equal
  python scripts/portfolio.py simulate --initial 1000000 --rate 7 --years 20
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.portfolio import Portfolio, Watchlist
from src.data.yahoo_client import YahooClient
from src.output.portfolio_formatter import (
    format_portfolio_summary,
    format_rebalance,
    format_compound_simulation,
)


def _get_current_prices(tickers: list) -> dict:
    """現在株価を一括取得"""
    client = YahooClient()
    prices = {}
    for ticker in tickers:
        price = client.get_price(ticker)
        if price:
            prices[ticker] = price
    return prices


def main():
    parser = argparse.ArgumentParser(description="ポートフォリオ管理")
    subparsers = parser.add_subparsers(dest="action")

    # summary
    subparsers.add_parser("summary", help="ポートフォリオサマリーを表示")

    # buy
    buy_p = subparsers.add_parser("buy", help="買い記録を追加")
    buy_p.add_argument("--ticker", "-t", required=True)
    buy_p.add_argument("--shares", "-s", type=float, required=True)
    buy_p.add_argument("--price", "-p", type=float, required=True)
    buy_p.add_argument("--name", "-n", default="")
    buy_p.add_argument("--commission", "-c", type=float, default=0.0)
    buy_p.add_argument("--date", "-d", default=None, help="取引日 (YYYY-MM-DD)")
    buy_p.add_argument("--note", default="")

    # sell
    sell_p = subparsers.add_parser("sell", help="売り記録を追加")
    sell_p.add_argument("--ticker", "-t", required=True)
    sell_p.add_argument("--shares", "-s", type=float, required=True)
    sell_p.add_argument("--price", "-p", type=float, required=True)
    sell_p.add_argument("--commission", "-c", type=float, default=0.0)
    sell_p.add_argument("--date", "-d", default=None)
    sell_p.add_argument("--note", default="")

    # history
    subparsers.add_parser("history", help="売買履歴を表示")

    # rebalance
    rb_p = subparsers.add_parser("rebalance", help="リバランス提案")
    rb_p.add_argument("--equal", action="store_true", help="均等ウェイトにリバランス")

    # simulate
    sim_p = subparsers.add_parser("simulate", help="複利シミュレーション")
    sim_p.add_argument("--initial", type=float, required=True, help="初期投資額")
    sim_p.add_argument("--rate", type=float, default=7.0, help="年間リターン率(%)")
    sim_p.add_argument("--dividend", type=float, default=0.0, help="配当利回り(%)")
    sim_p.add_argument("--years", type=int, default=20, help="シミュレーション年数")
    sim_p.add_argument("--monthly", type=float, default=0.0, help="毎月積立額")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        return

    pf = Portfolio()

    if args.action == "summary":
        holdings = pf.get_holdings()
        if not holdings:
            print("ポートフォリオは空です。`portfolio.py buy` で売買記録を追加してください。")
            return
        tickers = list(holdings.keys())
        print(f"株価を取得中... ({', '.join(tickers)})")
        prices = _get_current_prices(tickers)
        summary = pf.get_summary(prices)
        print(format_portfolio_summary(summary))

    elif args.action in ("buy", "sell"):
        ticker = args.ticker.upper()
        name = args.name
        if not name:
            try:
                client = YahooClient()
                info = client.get_info(ticker)
                if info:
                    name = info.get("longName") or info.get("shortName") or ticker
            except Exception:
                name = ticker

        result = pf.add_trade(
            ticker=ticker,
            name=name,
            action=args.action,
            shares=args.shares,
            price=args.price,
            commission=args.commission,
            trade_date=args.date,
            note=args.note,
        )
        if "error" in result:
            print(f"エラー: {result['error']}")
        else:
            action_jp = "買い" if args.action == "buy" else "売り"
            amount = args.shares * args.price + (args.commission or 0)
            print(f"✅ {ticker} {action_jp}記録を追加しました")
            print(f"   {args.shares}株 × {args.price:,.2f} = {amount:,.0f} (手数料: {args.commission:,.0f})")

    elif args.action == "history":
        records = pf.get_all_records()
        if not records:
            print("売買記録がありません")
            return
        print(f"## 売買履歴 ({len(records)}件)\n")
        print("| ID | ティッカー | アクション | 株数 | 価格 | 金額 | 手数料 | 日付 | メモ |")
        print("|---|-----------|---------|------|-----|-----|-------|------|-----|")
        for r in records:
            amount = r["shares"] * r["price"]
            action_jp = "買" if r["action"] == "buy" else "売"
            print(
                f"| {r['id']} | {r['ticker']} | {action_jp} | "
                f"{r['shares']:.1f} | {r['price']:,.2f} | {amount:,.0f} | "
                f"{r['commission']:,.0f} | {r['date']} | {r.get('note', '')} |"
            )

    elif args.action == "rebalance":
        holdings = pf.get_holdings()
        if not holdings:
            print("保有銘柄がありません")
            return
        prices = _get_current_prices(list(holdings.keys()))
        summary = pf.get_summary(prices)
        total_value = summary["total_market_value"]

        suggestions = pf.rebalance_suggestions(prices, equal_weight=args.equal)
        print(format_rebalance(suggestions, total_value))

    elif args.action == "simulate":
        params = {
            "initial_investment": args.initial,
            "annual_return_pct": args.rate,
            "annual_dividend_pct": args.dividend,
            "years": args.years,
            "monthly_contribution": args.monthly,
        }
        results = pf.compound_simulation(**params)
        print(format_compound_simulation(results, params))


if __name__ == "__main__":
    main()
