"""
リスク分析モジュールのテスト
"""

import pytest

from src.core.risk import RiskAnalyzer, STRESS_SCENARIOS


@pytest.fixture
def analyzer():
    return RiskAnalyzer()


@pytest.fixture
def sample_holdings():
    return [
        {"ticker": "7203.T", "sector": "Consumer Discretionary", "market_value": 500_000, "beta": 1.1},
        {"ticker": "9432.T", "sector": "Communication Services", "market_value": 300_000, "beta": 0.7},
        {"ticker": "8306.T", "sector": "Financials", "market_value": 200_000, "beta": 1.2},
    ]


class TestRiskAnalyzer:
    def test_stress_test_all_scenarios(self, analyzer, sample_holdings):
        result = analyzer.stress_test(sample_holdings, total_value=1_000_000)
        assert "scenarios" in result
        assert len(result["scenarios"]) == len(STRESS_SCENARIOS)

    def test_stress_test_specific_scenario(self, analyzer, sample_holdings):
        result = analyzer.stress_test(
            sample_holdings, total_value=1_000_000,
            scenarios=["market_crash"]
        )
        assert "market_crash" in result["scenarios"]
        assert len(result["scenarios"]) == 1

    def test_market_crash_loss(self, analyzer, sample_holdings):
        result = analyzer.stress_test(sample_holdings, total_value=1_000_000)
        crash = result["scenarios"]["market_crash"]
        assert crash["portfolio_change"] < 0  # 損失が発生
        assert crash["portfolio_change_pct"] < -30  # 30%以上の損失

    def test_worst_scenario_identified(self, analyzer, sample_holdings):
        result = analyzer.stress_test(sample_holdings, total_value=1_000_000)
        assert result["worst_scenario"] is not None
        worst = result["scenarios"][result["worst_scenario"]]
        for key, s in result["scenarios"].items():
            assert s["portfolio_change_pct"] >= worst["portfolio_change_pct"]

    def test_best_scenario_identified(self, analyzer, sample_holdings):
        result = analyzer.stress_test(sample_holdings, total_value=1_000_000)
        assert result["best_scenario"] is not None

    def test_holding_impacts_count(self, analyzer, sample_holdings):
        result = analyzer.stress_test(
            sample_holdings, total_value=1_000_000,
            scenarios=["market_crash"]
        )
        crash = result["scenarios"]["market_crash"]
        assert len(crash["holding_impacts"]) == len(sample_holdings)

    def test_post_shock_value_positive(self, analyzer, sample_holdings):
        """ショック後の資産はゼロ以上であること"""
        result = analyzer.stress_test(sample_holdings, total_value=1_000_000)
        for key, s in result["scenarios"].items():
            assert s["post_shock_value"] >= 0

    def test_calculate_var(self, analyzer):
        returns = [-2.0, -1.5, -1.0, 0.5, 1.0, 1.5, 2.0, -0.5, 0.0, 3.0]
        result = analyzer.calculate_var(returns, confidence_level=0.95)
        assert "var_pct" in result
        assert result["confidence_level"] == 0.95
        assert result["data_points"] == 10

    def test_calculate_var_insufficient_data(self, analyzer):
        result = analyzer.calculate_var([1.0, 2.0], confidence_level=0.95)
        assert "error" in result

    def test_sharpe_ratio(self, analyzer):
        returns = [0.07, 0.10, 0.05, 0.08, 0.12]
        sharpe = analyzer.calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        assert sharpe is not None
        assert isinstance(sharpe, float)

    def test_sharpe_ratio_insufficient_data(self, analyzer):
        result = analyzer.calculate_sharpe_ratio([0.05])
        assert result is None

    def test_max_drawdown(self, analyzer):
        prices = [100, 110, 90, 95, 80, 105, 120]
        result = analyzer.calculate_max_drawdown(prices)
        assert "max_drawdown_pct" in result
        assert result["max_drawdown_pct"] < 0  # ドローダウンは負の値

    def test_max_drawdown_no_decline(self, analyzer):
        prices = [100, 110, 120, 130]
        result = analyzer.calculate_max_drawdown(prices)
        assert result["max_drawdown_pct"] == 0.0

    def test_portfolio_beta(self, analyzer, sample_holdings):
        total_value = sum(h["market_value"] for h in sample_holdings)
        beta = analyzer.portfolio_beta(sample_holdings, total_value)
        assert beta is not None
        # 加重平均ベータ: (500000*1.1 + 300000*0.7 + 200000*1.2) / 1000000
        expected = (500_000 * 1.1 + 300_000 * 0.7 + 200_000 * 1.2) / 1_000_000
        assert beta == pytest.approx(expected, rel=0.01)

    def test_list_scenarios(self, analyzer):
        scenarios = analyzer.list_scenarios()
        assert len(scenarios) == len(STRESS_SCENARIOS)
        for s in scenarios:
            assert "key" in s
            assert "name" in s
            assert "description" in s
            assert "market_shock_pct" in s
