#!/usr/bin/env python3
"""
個別銘柄レポートスクリプト
Usage:
  python scripts/stock_report.py --ticker 7203.T
  python scripts/stock_report.py --ticker AAPL MSFT GOOGL  # 比較分析
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.research import ResearchEngine
from src.output.report_formatter import format_stock_report


def main():
    parser = argparse.ArgumentParser(description="個別銘柄分析レポート")
    parser.add_argument("--ticker", "-t", nargs="+", required=True, help="ティッカーシンボル (複数指定で比較)")
    parser.add_argument("--no-trap-check", action="store_true", help="バリュートラップチェックをスキップ")

    args = parser.parse_args()

    engine = ResearchEngine()

    if len(args.ticker) == 1:
        ticker = args.ticker[0].upper()
        print(f"{ticker} を分析中...\n")
        analysis = engine.analyze_stock(ticker)
        print(format_stock_report(analysis))
    else:
        print(f"{', '.join(args.ticker)} を比較分析中...\n")
        for ticker in args.ticker:
            t = ticker.upper()
            print(f"=== {t} ===")
            analysis = engine.analyze_stock(t)
            print(format_stock_report(analysis))
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
