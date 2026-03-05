"""
スクリーニングエンジンのテスト
"""

import pytest

from src.core.screening import ScreeningEngine


@pytest.fixture
def engine(tmp_path):
    """テスト用設定ファイルを使用するエンジン"""
    return ScreeningEngine(
        presets_path="config/screening_presets.yaml",
        exchanges_path="config/exchanges.yaml",
    )


class TestScreeningEngine:
    def test_list_presets(self, engine):
        presets = engine.list_presets()
        assert len(presets) == 15
        names = [p["name"] for p in presets]
        assert "value" in names
        assert "high_dividend" in names
        assert "deep_value" in names
        assert "global_value" in names

    def test_list_regions(self, engine):
        regions = engine.list_regions()
        assert len(regions) >= 20
        codes = [r["name"] for r in regions]
        assert "japan" in codes
        assert "us" in codes
        assert "hong_kong" in codes
        assert "germany" in codes

    def test_invalid_preset(self, engine):
        result = engine.screen(preset_name="nonexistent_preset")
        assert "error" in result
        assert "available_presets" in result

    def test_passes_filters_per(self, engine):
        """PERフィルタのテスト"""
        metrics_pass = {"per": 10.0, "pbr": 1.0, "roe": 10.0,
                        "market_cap_billion": 100, "dividend_yield": 3.0}
        metrics_fail = {"per": 20.0, "pbr": 1.0, "roe": 10.0,
                        "market_cap_billion": 100, "dividend_yield": 3.0}
        filters = {"per_max": 15.0}
        assert engine._passes_filters(metrics_pass, filters) is True
        assert engine._passes_filters(metrics_fail, filters) is False

    def test_passes_filters_pbr(self, engine):
        """PBRフィルタのテスト"""
        metrics_pass = {"pbr": 1.0}
        metrics_fail = {"pbr": 2.0}
        filters = {"pbr_max": 1.5}
        assert engine._passes_filters(metrics_pass, filters) is True
        assert engine._passes_filters(metrics_fail, filters) is False

    def test_passes_filters_roe(self, engine):
        """ROEフィルタのテスト"""
        metrics_pass = {"roe": 10.0}
        metrics_fail = {"roe": 3.0}
        filters = {"roe_min": 8.0}
        assert engine._passes_filters(metrics_pass, filters) is True
        assert engine._passes_filters(metrics_fail, filters) is False

    def test_passes_filters_market_cap(self, engine):
        """時価総額フィルタのテスト"""
        metrics_pass = {"market_cap_billion": 50.0}
        metrics_fail = {"market_cap_billion": 5.0}
        filters = {"market_cap_min_billion": 10.0}
        assert engine._passes_filters(metrics_pass, filters) is True
        assert engine._passes_filters(metrics_fail, filters) is False

    def test_passes_filters_dividend(self, engine):
        """配当利回りフィルタのテスト"""
        metrics_pass = {"dividend_yield": 4.0}
        metrics_fail = {"dividend_yield": 1.0}
        filters = {"dividend_yield_min": 0.03}  # 3%
        assert engine._passes_filters(metrics_pass, filters) is True
        assert engine._passes_filters(metrics_fail, filters) is False

    def test_passes_filters_none_values(self, engine):
        """Noneの場合はフィルタ失敗になること"""
        metrics = {"per": None, "pbr": None}
        filters = {"per_max": 15.0}
        assert engine._passes_filters(metrics, filters) is False

    def test_calculate_score_range(self, engine):
        """スコアが0-100の範囲内であること"""
        metrics = {
            "per": 10.0, "pbr": 0.8, "roe": 20.0,
            "dividend_yield": 4.0,
            "current_price": 1500, "52w_high": 2000, "52w_low": 1000,
        }
        weights = {
            "per_weight": 0.2, "pbr_weight": 0.2, "roe_weight": 0.2,
            "dividend_weight": 0.2, "momentum_weight": 0.2,
        }
        score = engine._calculate_score(metrics, weights)
        assert 0 <= score <= 100

    def test_calculate_score_higher_for_better_metrics(self, engine):
        """より良い指標はより高いスコアになること"""
        metrics_good = {
            "per": 5.0, "pbr": 0.3, "roe": 30.0,
            "dividend_yield": 8.0,
            "current_price": 1000, "52w_high": 2000, "52w_low": 900,
        }
        metrics_bad = {
            "per": 40.0, "pbr": 4.5, "roe": 1.0,
            "dividend_yield": 0.1,
            "current_price": 1900, "52w_high": 2000, "52w_low": 900,
        }
        weights = {
            "per_weight": 0.2, "pbr_weight": 0.2, "roe_weight": 0.2,
            "dividend_weight": 0.2, "momentum_weight": 0.2,
        }
        score_good = engine._calculate_score(metrics_good, weights)
        score_bad = engine._calculate_score(metrics_bad, weights)
        assert score_good > score_bad

    def test_collect_tickers_japan(self, engine):
        """日本地域のティッカーが取得できること"""
        tickers = engine._collect_tickers(["japan"], allowed_sectors=None)
        assert len(tickers) > 0
        assert all(".T" in t for t in tickers)

    def test_collect_tickers_multiple_regions(self, engine):
        """複数地域のティッカーが取得できること"""
        tickers = engine._collect_tickers(["japan", "us"], allowed_sectors=None)
        japan_tickers = [t for t in tickers if ".T" in t]
        us_tickers = [t for t in tickers if "." not in t]
        assert len(japan_tickers) > 0
        assert len(us_tickers) > 0

    def test_no_duplicate_tickers(self, engine):
        """ティッカーが重複しないこと"""
        tickers = engine._collect_tickers(["japan", "japan"], allowed_sectors=None)
        assert len(tickers) == len(set(tickers))
