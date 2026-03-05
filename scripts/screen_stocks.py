#!/usr/bin/env python3
"""
スクリーニングスクリプト
Usage:
  python scripts/screen_stocks.py --preset value --region japan us --limit 20
  python scripts/screen_stocks.py --list-presets
  python scripts/screen_stocks.py --list-regions
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.screening import ScreeningEngine
from src.output.screening_formatter import (
    format_screening_results,
    format_preset_list,
    format_region_list,
)


def main():
    parser = argparse.ArgumentParser(description="株式スクリーニングツール")
    parser.add_argument("--preset", "-p", default="value", help="スクリーニングプリセット名")
    parser.add_argument("--region", "-r", nargs="+", default=["japan", "us"], help="対象地域 (複数指定可)")
    parser.add_argument("--limit", "-l", type=int, default=20, help="最大表示件数")
    parser.add_argument("--details", "-d", action="store_true", help="詳細情報を表示")
    parser.add_argument("--list-presets", action="store_true", help="利用可能なプリセット一覧を表示")
    parser.add_argument("--list-regions", action="store_true", help="利用可能な地域一覧を表示")
    # カスタムフィルタ
    parser.add_argument("--per-max", type=float, help="PER上限")
    parser.add_argument("--pbr-max", type=float, help="PBR上限")
    parser.add_argument("--roe-min", type=float, help="ROE下限(%)")
    parser.add_argument("--div-min", type=float, help="配当利回り下限(%)")

    args = parser.parse_args()

    engine = ScreeningEngine()

    if args.list_presets:
        presets = engine.list_presets()
        print(format_preset_list(presets))
        return

    if args.list_regions:
        regions = engine.list_regions()
        print(format_region_list(regions))
        return

    # カスタムフィルタの組み立て
    custom_filters = {}
    if args.per_max:
        custom_filters["per_max"] = args.per_max
    if args.pbr_max:
        custom_filters["pbr_max"] = args.pbr_max
    if args.roe_min:
        custom_filters["roe_min"] = args.roe_min
    if args.div_min:
        custom_filters["dividend_yield_min"] = args.div_min / 100

    print(f"スクリーニング中... (プリセット: {args.preset}, 地域: {', '.join(args.region)})\n")

    result = engine.screen(
        preset_name=args.preset,
        regions=args.region,
        limit=args.limit,
        custom_filters=custom_filters or None,
    )

    print(format_screening_results(result, show_details=args.details))


if __name__ == "__main__":
    main()
