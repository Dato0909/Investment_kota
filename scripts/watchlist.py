#!/usr/bin/env python3
"""
ウォッチリスト管理スクリプト
Usage:
  python scripts/watchlist.py show
  python scripts/watchlist.py add --ticker 7203.T --name トヨタ --target 2500
  python scripts/watchlist.py remove --ticker 7203.T
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.portfolio import Watchlist
from src.data.yahoo_client import YahooClient
from src.output.portfolio_formatter import format_watchlist


def main():
    parser = argparse.ArgumentParser(description="ウォッチリスト管理")
    subparsers = parser.add_subparsers(dest="action", help="アクション")

    # show
    show_parser = subparsers.add_parser("show", help="ウォッチリストを表示")
    show_parser.add_argument("--no-price", action="store_true", help="現在株価を取得しない")

    # add
    add_parser = subparsers.add_parser("add", help="銘柄を追加")
    add_parser.add_argument("--ticker", "-t", required=True, help="ティッカーシンボル")
    add_parser.add_argument("--name", "-n", default="", help="銘柄名")
    add_parser.add_argument("--target", type=float, default=0.0, help="目標価格")
    add_parser.add_argument("--note", default="", help="メモ")

    # remove
    rm_parser = subparsers.add_parser("remove", help="銘柄を削除")
    rm_parser.add_argument("--ticker", "-t", required=True, help="ティッカーシンボル")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        return

    wl = Watchlist()

    if args.action == "show":
        records = wl.get_all()
        current_prices = None
        if not args.no_price and records:
            client = YahooClient()
            current_prices = {}
            for r in records:
                ticker = r["ticker"]
                price = client.get_price(ticker)
                if price:
                    current_prices[ticker] = price
        print(format_watchlist(records, current_prices))

    elif args.action == "add":
        ticker = args.ticker.upper()
        name = args.name
        if not name:
            # Yahoo Finance から名前を取得を試みる
            try:
                client = YahooClient()
                info = client.get_info(ticker)
                if info:
                    name = info.get("longName") or info.get("shortName") or ticker
            except Exception:
                name = ticker

        result = wl.add(ticker, name=name, target_price=args.target, note=args.note)
        if "error" in result:
            print(f"エラー: {result['error']}")
        else:
            print(f"✅ {ticker} ({name}) をウォッチリストに追加しました")

    elif args.action == "remove":
        ticker = args.ticker.upper()
        success = wl.remove(ticker)
        if success:
            print(f"✅ {ticker} をウォッチリストから削除しました")
        else:
            print(f"エラー: {ticker} はウォッチリストに見つかりません")


if __name__ == "__main__":
    main()
