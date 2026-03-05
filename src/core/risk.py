"""
リスク分析・ストレステストモジュール
8つのシナリオでポートフォリオへの影響を分析します
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


# ストレステストシナリオ定義
STRESS_SCENARIOS = {
    "market_crash": {
        "name": "市場暴落",
        "description": "リーマンショック級の市場暴落 (-40%)",
        "market_shock": -0.40,
        "sector_adjustments": {
            "Technology": -0.50,
            "Financials": -0.55,
            "Energy": -0.45,
            "Healthcare": -0.25,
            "Utilities": -0.20,
            "Consumer Staples": -0.20,
        },
    },
    "rate_hike": {
        "name": "急激な金利上昇",
        "description": "FRBによる急激な利上げ (金利+3%)",
        "market_shock": -0.20,
        "sector_adjustments": {
            "Technology": -0.30,
            "Real Estate": -0.35,
            "Utilities": -0.25,
            "Financials": +0.10,
            "Energy": +0.05,
            "Consumer Staples": -0.10,
        },
    },
    "yen_appreciation": {
        "name": "急激な円高",
        "description": "円高進行 (1ドル=100円水準)",
        "market_shock": -0.15,
        "sector_adjustments": {
            "Industrials": -0.25,
            "Consumer Discretionary": -0.20,
            "Technology": -0.15,
            "Materials": -0.10,
            "Healthcare": -0.05,
        },
        "currency_effect": "JPY_UP",
    },
    "inflation_surge": {
        "name": "インフレ急騰",
        "description": "インフレ率が8%超に急上昇",
        "market_shock": -0.18,
        "sector_adjustments": {
            "Energy": +0.15,
            "Materials": +0.10,
            "Real Estate": +0.05,
            "Consumer Staples": -0.05,
            "Technology": -0.25,
            "Consumer Discretionary": -0.20,
        },
    },
    "geopolitical_risk": {
        "name": "地政学リスク",
        "description": "中東・東アジア地域での紛争勃発",
        "market_shock": -0.20,
        "sector_adjustments": {
            "Energy": +0.20,
            "Defense": +0.15,
            "Technology": -0.15,
            "Consumer Discretionary": -0.20,
            "Travel": -0.40,
        },
    },
    "tech_bubble_burst": {
        "name": "テックバブル崩壊",
        "description": "AIバブル崩壊・テック株の急落",
        "market_shock": -0.25,
        "sector_adjustments": {
            "Technology": -0.50,
            "Communication Services": -0.40,
            "Consumer Discretionary": -0.20,
            "Financials": -0.15,
            "Healthcare": -0.05,
            "Utilities": +0.05,
            "Energy": +0.05,
        },
    },
    "pandemic": {
        "name": "新型パンデミック",
        "description": "COVID-19級のパンデミック再来",
        "market_shock": -0.30,
        "sector_adjustments": {
            "Healthcare": +0.10,
            "Technology": +0.05,
            "Consumer Staples": -0.05,
            "Travel": -0.60,
            "Retail": -0.30,
            "Energy": -0.40,
            "Financials": -0.25,
        },
    },
    "mild_recession": {
        "name": "軽度な景気後退",
        "description": "軽度な景気後退・企業業績悪化",
        "market_shock": -0.15,
        "sector_adjustments": {
            "Consumer Discretionary": -0.20,
            "Industrials": -0.15,
            "Financials": -0.10,
            "Consumer Staples": -0.05,
            "Healthcare": -0.05,
            "Utilities": -0.03,
        },
    },
}


class RiskAnalyzer:
    """ポートフォリオリスク分析クラス"""

    def stress_test(
        self,
        holdings: List[Dict[str, Any]],
        total_value: float,
        scenarios: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        ストレステストを実行

        Args:
            holdings: 保有銘柄リスト [{ticker, market_value, sector, ...}]
            total_value: ポートフォリオ合計時価総額
            scenarios: 実行するシナリオ名リスト (Noneで全シナリオ)

        Returns:
            各シナリオの損失額・損失率・銘柄別影響
        """
        target_scenarios = scenarios or list(STRESS_SCENARIOS.keys())
        results = {}

        for scenario_key in target_scenarios:
            scenario = STRESS_SCENARIOS.get(scenario_key)
            if not scenario:
                continue

            scenario_result = self._run_scenario(holdings, total_value, scenario)
            results[scenario_key] = {
                "name": scenario["name"],
                "description": scenario["description"],
                **scenario_result,
            }

        # 最悪シナリオの特定
        if results:
            worst_key = min(results, key=lambda k: results[k]["portfolio_change_pct"])
            best_key = max(results, key=lambda k: results[k]["portfolio_change_pct"])
        else:
            worst_key = best_key = None

        return {
            "total_value": total_value,
            "scenarios": results,
            "worst_scenario": worst_key,
            "best_scenario": best_key,
        }

    def _run_scenario(
        self,
        holdings: List[Dict[str, Any]],
        total_value: float,
        scenario: Dict[str, Any],
    ) -> Dict[str, Any]:
        """単一シナリオの影響を計算"""
        market_shock = scenario.get("market_shock", 0.0)
        sector_adjustments = scenario.get("sector_adjustments", {})

        holding_impacts = []
        total_loss = 0.0

        for h in holdings:
            ticker = h.get("ticker", "")
            sector = h.get("sector") or "Unknown"
            market_value = h.get("market_value") or 0.0

            # セクター調整込みのショック率計算
            sector_adj = sector_adjustments.get(sector, 0.0)
            effective_shock = market_shock + sector_adj * 0.5  # セクター効果を50%適用
            effective_shock = max(-0.95, min(0.5, effective_shock))  # クランプ

            loss = market_value * effective_shock
            total_loss += loss

            holding_impacts.append({
                "ticker": ticker,
                "sector": sector,
                "market_value": market_value,
                "effective_shock_pct": round(effective_shock * 100, 1),
                "estimated_loss": round(loss, 0),
                "post_shock_value": round(market_value + loss, 0),
            })

        portfolio_change = total_loss
        portfolio_change_pct = (total_loss / total_value * 100) if total_value > 0 else 0.0

        holding_impacts.sort(key=lambda x: x["estimated_loss"])

        return {
            "portfolio_change": round(portfolio_change, 0),
            "portfolio_change_pct": round(portfolio_change_pct, 2),
            "post_shock_value": round(total_value + portfolio_change, 0),
            "holding_impacts": holding_impacts,
        }

    def calculate_var(
        self,
        returns: List[float],
        confidence_level: float = 0.95,
    ) -> Dict[str, float]:
        """
        VaR (Value at Risk) を計算
        Args:
            returns: 日次リターンのリスト (%)
            confidence_level: 信頼水準 (デフォルト95%)
        """
        if len(returns) < 10:
            return {"error": "データ不足 (最低10日分のリターンデータが必要)"}

        arr = np.array(returns)
        var_pct = np.percentile(arr, (1 - confidence_level) * 100)
        cvar_pct = arr[arr <= var_pct].mean() if len(arr[arr <= var_pct]) > 0 else var_pct

        return {
            "var_pct": round(float(var_pct), 4),
            "cvar_pct": round(float(cvar_pct), 4),
            "confidence_level": confidence_level,
            "data_points": len(returns),
        }

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02,
    ) -> Optional[float]:
        """
        シャープレシオを計算
        Args:
            returns: 年次リターン率のリスト
            risk_free_rate: リスクフリーレート (デフォルト2%)
        """
        if len(returns) < 2:
            return None
        arr = np.array(returns)
        excess_returns = arr - risk_free_rate
        if arr.std() == 0:
            return None
        sharpe = excess_returns.mean() / arr.std()
        return round(float(sharpe), 4)

    def calculate_max_drawdown(self, prices: List[float]) -> Dict[str, float]:
        """
        最大ドローダウンを計算
        Args:
            prices: 株価または資産価値の時系列リスト
        """
        if len(prices) < 2:
            return {"max_drawdown_pct": 0.0}

        arr = np.array(prices)
        peak = arr[0]
        max_dd = 0.0
        peak_idx = 0
        trough_idx = 0

        for i in range(1, len(arr)):
            if arr[i] > peak:
                peak = arr[i]
                peak_idx = i
            dd = (arr[i] - peak) / peak
            if dd < max_dd:
                max_dd = dd
                trough_idx = i

        return {
            "max_drawdown_pct": round(max_dd * 100, 4),
            "peak_index": peak_idx,
            "trough_index": trough_idx,
        }

    def portfolio_beta(
        self,
        holdings: List[Dict[str, Any]],
        total_value: float,
    ) -> Optional[float]:
        """
        ポートフォリオ加重平均ベータを計算
        Args:
            holdings: [{ticker, market_value, beta}, ...]
            total_value: ポートフォリオ合計時価総額
        """
        if total_value <= 0:
            return None

        weighted_beta = 0.0
        covered_value = 0.0

        for h in holdings:
            beta = h.get("beta")
            mv = h.get("market_value") or 0.0
            if beta is not None and mv > 0:
                weighted_beta += beta * mv
                covered_value += mv

        if covered_value <= 0:
            return None

        return round(weighted_beta / covered_value, 4)

    def list_scenarios(self) -> List[Dict[str, str]]:
        """ストレステストシナリオ一覧を返す"""
        return [
            {
                "key": key,
                "name": s["name"],
                "description": s["description"],
                "market_shock_pct": round(s["market_shock"] * 100, 1),
            }
            for key, s in STRESS_SCENARIOS.items()
        ]
