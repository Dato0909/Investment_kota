"""
出力フォーマッタのテスト
"""

import pytest

from src.output.screening_formatter import format_screening_results, format_preset_list
from src.output.portfolio_formatter import (
    format_watchlist,
    format_compound_simulation,
    format_stress_test,
)
from src.output.report_formatter import format_stock_report


class TestScreeningFormatter:
    def test_format_results_with_data(self):
        result = {
            "preset_name": "value",
            "preset_label": "バリュー投資",
            "preset_description": "低PER・低PBRの割安株",
            "regions": ["japan"],
            "total_screened": 15,
            "total_filtered": 5,
            "results": [
                {
                    "ticker": "7203.T",
                    "name": "トヨタ自動車",
                    "score": 75.5,
                    "per": 8.5,
                    "pbr": 0.9,
                    "roe": 12.0,
                    "dividend_yield": 3.5,
                    "market_cap_billion": 300.0,
                    "sector": "Consumer Discretionary",
                }
            ],
        }
        output = format_screening_results(result)
        assert "バリュー投資" in output
        assert "7203.T" in output
        assert "75.5" in output

    def test_format_results_empty(self):
        result = {
            "preset_name": "value",
            "preset_label": "バリュー投資",
            "preset_description": "",
            "regions": ["japan"],
            "total_screened": 10,
            "total_filtered": 0,
            "results": [],
        }
        output = format_screening_results(result)
        assert "見つかりませんでした" in output

    def test_format_results_error(self):
        result = {
            "error": "プリセット 'xxx' が見つかりません",
            "available_presets": ["value", "high_dividend"],
        }
        output = format_screening_results(result)
        assert "エラー" in output
        assert "value" in output

    def test_format_preset_list(self):
        presets = [
            {"name": "value", "label": "バリュー投資", "description": "低PER"},
            {"name": "high_dividend", "label": "高配当", "description": "配当重視"},
        ]
        output = format_preset_list(presets)
        assert "バリュー投資" in output
        assert "高配当" in output
        assert "`value`" in output


class TestPortfolioFormatter:
    def test_format_watchlist_empty(self):
        output = format_watchlist([])
        assert "空です" in output

    def test_format_watchlist_with_data(self):
        records = [
            {
                "ticker": "7203.T",
                "name": "トヨタ自動車",
                "added_date": "2024-01-01",
                "target_price": "3000",
                "note": "配当注目",
            }
        ]
        output = format_watchlist(records)
        assert "7203.T" in output
        assert "トヨタ自動車" in output

    def test_format_watchlist_with_prices(self):
        records = [{"ticker": "7203.T", "name": "トヨタ", "added_date": "2024-01-01", "target_price": "", "note": ""}]
        prices = {"7203.T": 2500.0}
        output = format_watchlist(records, current_prices=prices)
        assert "2,500" in output

    def test_format_compound_simulation(self):
        params = {
            "initial_investment": 1_000_000,
            "annual_return_pct": 7.0,
            "annual_dividend_pct": 2.0,
            "years": 20,
            "monthly_contribution": 30_000,
        }
        from src.core.portfolio import Portfolio
        pf = Portfolio.__new__(Portfolio)
        results = pf.compound_simulation.__func__(pf,
            initial_investment=1_000_000,
            annual_return_pct=7.0,
            years=10,
        )

        output = format_compound_simulation(results, params)
        assert "複利シミュレーション" in output
        assert "1,000,000" in output

    def test_format_stress_test(self):
        result = {
            "total_value": 1_000_000,
            "worst_scenario": "market_crash",
            "best_scenario": "mild_recession",
            "scenarios": {
                "market_crash": {
                    "name": "市場暴落",
                    "description": "リーマン級",
                    "portfolio_change": -400_000,
                    "portfolio_change_pct": -40.0,
                    "post_shock_value": 600_000,
                    "holding_impacts": [],
                },
                "mild_recession": {
                    "name": "軽度な景気後退",
                    "description": "軽度",
                    "portfolio_change": -150_000,
                    "portfolio_change_pct": -15.0,
                    "post_shock_value": 850_000,
                    "holding_impacts": [],
                },
            },
        }
        output = format_stress_test(result)
        assert "ストレステスト" in output
        assert "市場暴落" in output
        assert "-40.00%" in output


class TestReportFormatter:
    def test_format_error(self):
        analysis = {"error": "データを取得できませんでした"}
        output = format_stock_report(analysis)
        assert "エラー" in output

    def test_format_full_report(self):
        analysis = {
            "ticker": "7203.T",
            "metrics": {
                "ticker": "7203.T",
                "name": "トヨタ自動車",
                "sector": "Consumer Discretionary",
                "industry": "Auto Manufacturers",
                "country": "Japan",
                "currency": "JPY",
                "current_price": 2500.0,
                "52w_high": 3000.0,
                "52w_low": 2000.0,
                "beta": 0.9,
                "market_cap_billion": 300.0,
                "per": 10.0,
                "pbr": 0.9,
                "roe": 12.0,
                "profit_margin": 8.0,
                "dividend_yield": 3.5,
                "payout_ratio": 35.0,
                "revenue_growth": 5.0,
                "current_ratio": 1.8,
                "debt_to_equity": 80.0,
            },
            "valuation": {
                "overall_score": 75,
                "overall_rating": "良好 (Good)",
                "per": {"value": 10.0, "rating": "割安", "score": 80, "comment": "割安圏"},
                "pbr": {"value": 0.9, "rating": "割安", "score": 80, "comment": "割安"},
                "psr": {"value": 0.5},
                "ev_ebitda": {"value": 6.0},
                "dividend_yield": {"value": 3.5, "rating": "中配当", "score": 70},
            },
            "health": {
                "overall_score": 70,
                "overall_rating": "良好 (Good)",
                "profitability": {"roe": 12.0, "roa": 5.0, "profit_margin": 8.0,
                                  "operating_margin": 10.0, "score": 65, "rating": "良好"},
                "safety": {"current_ratio": 1.8, "quick_ratio": 1.2,
                           "debt_to_equity": 80.0, "score": 70, "rating": "良好"},
                "growth": {"revenue_growth": 5.0, "earnings_growth": 8.0,
                           "score": 70, "rating": "良好"},
            },
            "value_trap": {
                "risk_level": "LOW",
                "verdict": "バリュートラップの可能性は低い",
                "red_flags": [],
                "warnings": [],
            },
            "summary": {
                "ticker": "7203.T",
                "name": "トヨタ自動車",
                "sector": "Consumer Discretionary",
                "valuation_score": 75,
                "health_score": 70,
                "trap_risk": "LOW",
                "total_score": 72,
                "recommendation": "Buy (買い候補)",
            },
        }
        output = format_stock_report(analysis)
        assert "7203.T" in output
        assert "トヨタ自動車" in output
        assert "Buy" in output
        assert "バリュートラップ" in output
        assert "PER" in output
