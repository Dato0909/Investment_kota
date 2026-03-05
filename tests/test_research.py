"""
銘柄調査モジュールのテスト
"""

import pytest

from src.core.research import (
    ResearchEngine,
    _rate_per,
    _rate_pbr,
    _rate_dividend,
    _score_profitability,
    _score_safety,
    _score_growth,
    _score_to_label,
)


class TestRatingFunctions:
    """個別レーティング関数のテスト"""

    def test_rate_per_none(self):
        result = _rate_per(None)
        assert result["label"] == "N/A"
        assert result["score"] is None

    def test_rate_per_negative(self):
        result = _rate_per(-5.0)
        assert result["label"] == "赤字"
        assert result["score"] < 20

    def test_rate_per_very_low(self):
        result = _rate_per(5.0)
        assert result["label"] == "超割安"
        assert result["score"] > 90

    def test_rate_per_low(self):
        result = _rate_per(12.0)
        assert result["label"] == "割安"
        assert result["score"] > 70

    def test_rate_per_high(self):
        result = _rate_per(50.0)
        assert result["label"] == "割高"
        assert result["score"] < 30

    def test_rate_pbr_none(self):
        result = _rate_pbr(None)
        assert result["label"] == "N/A"

    def test_rate_pbr_very_low(self):
        result = _rate_pbr(0.3)
        assert result["label"] == "超割安"
        assert result["score"] > 90

    def test_rate_pbr_normal(self):
        result = _rate_pbr(1.5)
        assert result["label"] == "適正"

    def test_rate_dividend_none(self):
        result = _rate_dividend(None)
        assert result["label"] == "無配"

    def test_rate_dividend_high(self):
        result = _rate_dividend(6.0)
        assert result["label"] == "高配当"

    def test_rate_dividend_medium(self):
        result = _rate_dividend(3.5)
        assert result["label"] == "中配当"


class TestScoringFunctions:
    def test_score_profitability_high(self):
        score = _score_profitability(roe=25.0, margin=20.0, op_margin=20.0)
        assert score is not None
        assert score >= 80

    def test_score_profitability_low(self):
        score = _score_profitability(roe=1.0, margin=0.5, op_margin=0.5)
        assert score is not None
        assert score < 20

    def test_score_profitability_none(self):
        score = _score_profitability(roe=None, margin=None, op_margin=None)
        assert score is None

    def test_score_profitability_partial(self):
        score = _score_profitability(roe=15.0, margin=None, op_margin=None)
        assert score is not None

    def test_score_safety_high(self):
        score = _score_safety(current_ratio=3.0, de_ratio=10.0)
        assert score >= 80

    def test_score_safety_low(self):
        score = _score_safety(current_ratio=0.5, de_ratio=300.0)
        assert score < 40

    def test_score_growth_high(self):
        score = _score_growth(rev_growth=20.0, earn_growth=25.0)
        assert score >= 80

    def test_score_growth_negative(self):
        score = _score_growth(rev_growth=-10.0, earn_growth=-20.0)
        assert score < 30

    def test_score_to_label_excellent(self):
        label = _score_to_label(85.0)
        assert "優秀" in label

    def test_score_to_label_good(self):
        label = _score_to_label(70.0)
        assert "良好" in label

    def test_score_to_label_poor(self):
        label = _score_to_label(20.0)
        assert "問題" in label

    def test_score_to_label_none(self):
        label = _score_to_label(None)
        assert label == "N/A"


class TestResearchEngine:
    def test_value_trap_red_flag_low_roe(self):
        """低ROEはレッドフラグになること"""
        engine = ResearchEngine()
        metrics = {
            "roe": 2.0, "revenue_growth": 5.0, "earnings_growth": 5.0,
            "debt_to_equity": 50.0, "current_ratio": 2.0,
            "payout_ratio": 40.0, "dividend_yield": 3.0, "profit_margin": 5.0,
        }
        result = engine._check_value_trap(metrics)
        assert any("ROE" in flag for flag in result["red_flags"])

    def test_value_trap_red_flag_high_debt(self):
        """高負債はレッドフラグになること"""
        engine = ResearchEngine()
        metrics = {
            "roe": 15.0, "revenue_growth": 5.0, "earnings_growth": 5.0,
            "debt_to_equity": 250.0, "current_ratio": 2.0,
            "payout_ratio": 40.0, "dividend_yield": 3.0, "profit_margin": 5.0,
        }
        result = engine._check_value_trap(metrics)
        assert any("負債" in flag for flag in result["red_flags"])

    def test_value_trap_low_risk(self):
        """良好な指標ではリスクLOW"""
        engine = ResearchEngine()
        metrics = {
            "roe": 20.0, "revenue_growth": 10.0, "earnings_growth": 10.0,
            "debt_to_equity": 30.0, "current_ratio": 2.5,
            "payout_ratio": 40.0, "dividend_yield": 3.0, "profit_margin": 15.0,
        }
        result = engine._check_value_trap(metrics)
        assert result["risk_level"] == "LOW"

    def test_value_trap_high_risk(self):
        """複数のレッドフラグはリスクHIGH"""
        engine = ResearchEngine()
        metrics = {
            "roe": 1.0,            # LOW ROE
            "revenue_growth": -15.0,  # declining revenue
            "earnings_growth": -20.0,
            "debt_to_equity": 300.0,  # high debt
            "current_ratio": 0.5,   # low liquidity
            "payout_ratio": 120.0,  # unsustainable dividend
            "dividend_yield": 8.0,
            "profit_margin": 0.5,   # very low margin
        }
        result = engine._check_value_trap(metrics)
        assert result["risk_level"] == "HIGH"

    def test_generate_summary_recommendation(self):
        """高スコアはStrong Buyになること"""
        engine = ResearchEngine()
        metrics = {"ticker": "TEST", "name": "Test Corp", "sector": "Technology"}
        valuation = {"overall_score": 85, "overall_rating": "優秀"}
        health = {"overall_score": 80, "overall_rating": "良好"}
        value_trap = {"risk_level": "LOW", "verdict": "低リスク"}
        summary = engine._generate_summary(metrics, valuation, health, value_trap)
        assert "Strong Buy" in summary["recommendation"] or "Buy" in summary["recommendation"]
