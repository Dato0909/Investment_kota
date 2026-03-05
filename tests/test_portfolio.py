"""
ポートフォリオ管理モジュールのテスト
"""

import tempfile
from pathlib import Path

import pytest

from src.core.portfolio import Portfolio, Watchlist, _hhi_risk_label


@pytest.fixture
def tmp_portfolio(tmp_path):
    return Portfolio(csv_path=str(tmp_path / "portfolio.csv"))


@pytest.fixture
def tmp_watchlist(tmp_path):
    return Watchlist(csv_path=str(tmp_path / "watchlist.csv"))


class TestPortfolio:
    def test_add_buy_trade(self, tmp_portfolio):
        result = tmp_portfolio.add_trade(
            ticker="7203.T", name="トヨタ", action="buy",
            shares=100, price=2500.0, commission=500.0
        )
        assert result["success"] is True
        assert result["record"]["ticker"] == "7203.T"
        assert result["record"]["shares"] == 100
        assert result["record"]["action"] == "buy"

    def test_add_sell_trade(self, tmp_portfolio):
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2500.0)
        result = tmp_portfolio.add_trade("7203.T", "トヨタ", "sell", 50, 2800.0)
        assert result["success"] is True

    def test_invalid_action(self, tmp_portfolio):
        result = tmp_portfolio.add_trade("7203.T", "トヨタ", "invalid", 100, 2500.0)
        assert "error" in result

    def test_invalid_shares(self, tmp_portfolio):
        result = tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", -10, 2500.0)
        assert "error" in result

    def test_invalid_price(self, tmp_portfolio):
        result = tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 0)
        assert "error" in result

    def test_get_holdings(self, tmp_portfolio):
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2500.0)
        tmp_portfolio.add_trade("6758.T", "ソニー", "buy", 50, 12000.0)
        holdings = tmp_portfolio.get_holdings()
        assert "7203.T" in holdings
        assert "6758.T" in holdings
        assert holdings["7203.T"]["total_shares"] == 100
        assert holdings["6758.T"]["total_shares"] == 50

    def test_holdings_net_zero_excluded(self, tmp_portfolio):
        """全て売った銘柄はholdingsから除外される"""
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2500.0)
        tmp_portfolio.add_trade("7203.T", "トヨタ", "sell", 100, 2800.0)
        holdings = tmp_portfolio.get_holdings()
        assert "7203.T" not in holdings

    def test_avg_cost_calculation(self, tmp_portfolio):
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2000.0)
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 3000.0)
        holdings = tmp_portfolio.get_holdings()
        # 平均取得価格 = (100*2000 + 100*3000) / 200 = 2500
        assert holdings["7203.T"]["avg_cost"] == pytest.approx(2500.0, rel=0.01)

    def test_calculate_pnl(self, tmp_portfolio):
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2000.0)
        prices = {"7203.T": 2500.0}
        pnl = tmp_portfolio.calculate_pnl(prices)
        assert len(pnl) == 1
        assert pnl[0]["ticker"] == "7203.T"
        assert pnl[0]["unrealized_pnl"] == pytest.approx(50000.0, rel=0.01)
        assert pnl[0]["unrealized_pnl_pct"] == pytest.approx(25.0, rel=0.01)

    def test_get_summary(self, tmp_portfolio):
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2000.0)
        tmp_portfolio.add_trade("6758.T", "ソニー", "buy", 50, 10000.0)
        prices = {"7203.T": 2500.0, "6758.T": 12000.0}
        summary = tmp_portfolio.get_summary(prices)

        assert summary["holdings_count"] == 2
        assert summary["total_market_value"] == pytest.approx(100 * 2500 + 50 * 12000)
        assert "hhi" in summary
        assert "allocation" in summary

    def test_hhi_single_stock(self, tmp_portfolio):
        """1銘柄のみの場合HHI=1.0 (最大集中)"""
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2000.0)
        prices = {"7203.T": 2000.0}
        summary = tmp_portfolio.get_summary(prices)
        assert summary["hhi"] == pytest.approx(1.0, rel=0.01)

    def test_rebalance_equal(self, tmp_portfolio):
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2000.0)
        tmp_portfolio.add_trade("6758.T", "ソニー", "buy", 10, 12000.0)
        prices = {"7203.T": 2000.0, "6758.T": 12000.0}
        suggestions = tmp_portfolio.rebalance_suggestions(prices, equal_weight=True)
        assert len(suggestions) == 2
        for s in suggestions:
            assert s["target_weight_pct"] == pytest.approx(50.0, rel=0.01)

    def test_compound_simulation(self, tmp_portfolio):
        results = tmp_portfolio.compound_simulation(
            initial_investment=1_000_000,
            annual_return_pct=7.0,
            years=10,
        )
        assert len(results) == 10
        assert results[0]["year"] == 1
        assert results[-1]["year"] == 10
        # 10年後の資産は初期投資より多いはず
        assert results[-1]["portfolio_value"] > 1_000_000

    def test_delete_record(self, tmp_portfolio):
        result = tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2500.0)
        record_id = result["record"]["id"]
        success = tmp_portfolio.delete_record(record_id)
        assert success is True
        records = tmp_portfolio.get_all_records()
        assert not any(str(r.get("id")) == str(record_id) for r in records)

    def test_multiple_ids_sequential(self, tmp_portfolio):
        tmp_portfolio.add_trade("7203.T", "トヨタ", "buy", 100, 2500.0)
        r2 = tmp_portfolio.add_trade("6758.T", "ソニー", "buy", 50, 12000.0)
        assert int(r2["record"]["id"]) == 2


class TestWatchlist:
    def test_add_and_get(self, tmp_watchlist):
        result = tmp_watchlist.add("7203.T", name="トヨタ", target_price=3000)
        assert result["success"] is True
        records = tmp_watchlist.get_all()
        assert len(records) == 1
        assert records[0]["ticker"] == "7203.T"

    def test_add_duplicate(self, tmp_watchlist):
        tmp_watchlist.add("7203.T", name="トヨタ")
        result = tmp_watchlist.add("7203.T", name="トヨタ")
        assert "error" in result

    def test_remove(self, tmp_watchlist):
        tmp_watchlist.add("7203.T", name="トヨタ")
        success = tmp_watchlist.remove("7203.T")
        assert success is True
        assert tmp_watchlist.get_all() == []

    def test_remove_nonexistent(self, tmp_watchlist):
        success = tmp_watchlist.remove("NOTEXIST")
        assert success is False

    def test_get_tickers(self, tmp_watchlist):
        tmp_watchlist.add("7203.T", name="トヨタ")
        tmp_watchlist.add("AAPL", name="Apple")
        tickers = tmp_watchlist.get_tickers()
        assert "7203.T" in tickers
        assert "AAPL" in tickers

    def test_case_insensitive(self, tmp_watchlist):
        tmp_watchlist.add("aapl", name="Apple")
        tickers = tmp_watchlist.get_tickers()
        assert "AAPL" in tickers


class TestHHIRiskLabel:
    def test_low_risk(self):
        assert "低リスク" in _hhi_risk_label(0.05)

    def test_medium_risk(self):
        assert "中リスク" in _hhi_risk_label(0.15)

    def test_high_risk(self):
        assert "高リスク" in _hhi_risk_label(0.20)

    def test_very_high_risk(self):
        assert "非常に高いリスク" in _hhi_risk_label(0.30)
