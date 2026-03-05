"""
スクリーニングエンジン
15の投資戦略プリセットを使って、複数地域から割安株をスクリーニングします
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..data.yahoo_client import YahooClient


class ScreeningEngine:
    """割安株スクリーニングエンジン"""

    def __init__(
        self,
        presets_path: str = "config/screening_presets.yaml",
        exchanges_path: str = "config/exchanges.yaml",
        cache_ttl_hours: float = 24.0,
    ):
        self.client = YahooClient(cache_ttl_hours=cache_ttl_hours)
        self.presets = self._load_yaml(presets_path).get("presets", {})
        self.exchanges = self._load_yaml(exchanges_path).get("regions", {})

    @staticmethod
    def _load_yaml(path: str) -> Dict:
        p = Path(path)
        if not p.exists():
            return {}
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    # ------------------------------------------------------------------
    # メインスクリーニング
    # ------------------------------------------------------------------

    def screen(
        self,
        preset_name: str = "value",
        regions: Optional[List[str]] = None,
        limit: int = 20,
        custom_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        指定プリセット・地域で銘柄をスクリーニングします

        Args:
            preset_name: プリセット名 (例: "value", "high_dividend")
            regions: 対象地域リスト (例: ["japan", "us"])
            limit: 最大取得件数
            custom_filters: プリセットを上書きするカスタムフィルタ

        Returns:
            {"preset": ..., "results": [...], "total_screened": ...}
        """
        preset = self.presets.get(preset_name)
        if not preset:
            available = list(self.presets.keys())
            return {
                "error": f"プリセット '{preset_name}' が見つかりません",
                "available_presets": available,
            }

        filters = dict(preset.get("filters", {}))
        if custom_filters:
            filters.update(custom_filters)

        scoring_weights = preset.get("scoring", {})
        allowed_sectors = preset.get("sectors")

        # 対象地域の決定
        target_regions = regions or ["japan", "us"]

        # 対象ティッカーの収集
        tickers = self._collect_tickers(target_regions, allowed_sectors)

        # データ取得
        all_metrics = self.client.get_multiple_metrics(tickers, delay=0.2)

        # フィルタリング
        filtered = [m for m in all_metrics if self._passes_filters(m, filters)]

        # スコアリング
        scored = [
            {**m, "score": self._calculate_score(m, scoring_weights)}
            for m in filtered
        ]

        # スコア降順ソート
        scored.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "preset_name": preset_name,
            "preset_label": preset.get("name", preset_name),
            "preset_description": preset.get("description", ""),
            "filters": filters,
            "regions": target_regions,
            "total_screened": len(all_metrics),
            "total_filtered": len(filtered),
            "results": scored[:limit],
        }

    def list_presets(self) -> List[Dict[str, str]]:
        """利用可能なプリセット一覧を返す"""
        return [
            {
                "name": key,
                "label": val.get("name", key),
                "description": val.get("description", ""),
            }
            for key, val in self.presets.items()
        ]

    def list_regions(self) -> List[Dict[str, str]]:
        """利用可能な地域一覧を返す"""
        return [
            {
                "name": key,
                "label": val.get("name", key),
                "exchange": val.get("exchange", ""),
                "currency": val.get("currency", ""),
            }
            for key, val in self.exchanges.items()
        ]

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    def _collect_tickers(self, regions: List[str], allowed_sectors: Optional[List[str]]) -> List[str]:
        """指定地域のサンプルティッカーを収集"""
        tickers = []
        for region in regions:
            exchange = self.exchanges.get(region, {})
            samples = exchange.get("sample_tickers", [])
            tickers.extend(samples)
        return list(dict.fromkeys(tickers))  # 重複除去・順序保持

    def _passes_filters(self, metrics: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """フィルタ条件をすべて満たすか判定"""
        def _val(key: str) -> Optional[float]:
            return metrics.get(key)

        # PER フィルタ
        if "per_max" in filters:
            per = _val("per")
            if per is None or per <= 0 or per > filters["per_max"]:
                return False

        # PBR フィルタ
        if "pbr_max" in filters:
            pbr = _val("pbr")
            if pbr is None or pbr <= 0 or pbr > filters["pbr_max"]:
                return False

        # ROE フィルタ
        if "roe_min" in filters:
            roe = _val("roe")
            if roe is None or roe < filters["roe_min"]:
                return False

        # 配当利回りフィルタ
        if "dividend_yield_min" in filters:
            dy = _val("dividend_yield")
            if dy is None or dy < filters["dividend_yield_min"] * 100:
                return False
        if "dividend_yield_max" in filters:
            dy = _val("dividend_yield")
            if dy is not None and dy > filters["dividend_yield_max"] * 100:
                return False

        # 配当性向フィルタ
        if "payout_ratio_max" in filters:
            pr = _val("payout_ratio")
            if pr is not None and pr > filters["payout_ratio_max"] * 100:
                return False

        # 負債比率フィルタ (D/E ratio)
        if "debt_ratio_max" in filters:
            de = _val("debt_to_equity")
            if de is not None and de > filters["debt_ratio_max"] * 100:
                return False

        # 時価総額フィルタ (億円換算)
        if "market_cap_min_billion" in filters:
            mc = _val("market_cap_billion")
            if mc is None or mc < filters["market_cap_min_billion"]:
                return False
        if "market_cap_max_billion" in filters:
            mc = _val("market_cap_billion")
            if mc is not None and mc > filters["market_cap_max_billion"]:
                return False

        # 利益率フィルタ
        if "profit_margin_min" in filters:
            pm = _val("profit_margin")
            if pm is None or pm < filters["profit_margin_min"] * 100:
                return False

        # 売上成長率フィルタ
        if "revenue_growth_min" in filters:
            rg = _val("revenue_growth")
            if rg is None or rg < filters["revenue_growth_min"] * 100:
                return False

        # ベータフィルタ
        if "beta_max" in filters:
            beta = _val("beta")
            if beta is not None and beta > filters["beta_max"]:
                return False

        return True

    def _calculate_score(self, metrics: Dict[str, Any], weights: Dict[str, float]) -> float:
        """
        重み付きスコアリング (0-100点)
        各指標を正規化して合計します
        """
        score = 0.0

        # PERスコア (低いほど高得点, 1-50の範囲)
        per_weight = weights.get("per_weight", 0.2)
        per = metrics.get("per")
        if per and 0 < per <= 50:
            per_score = max(0, (50 - per) / 50) * 100
            score += per_score * per_weight

        # PBRスコア (低いほど高得点, 0-5の範囲)
        pbr_weight = weights.get("pbr_weight", 0.2)
        pbr = metrics.get("pbr")
        if pbr and 0 < pbr <= 5:
            pbr_score = max(0, (5 - pbr) / 5) * 100
            score += pbr_score * pbr_weight

        # ROEスコア (高いほど高得点, 0-30%の範囲)
        roe_weight = weights.get("roe_weight", 0.2)
        roe = metrics.get("roe")
        if roe is not None:
            roe_score = min(100, max(0, roe / 30 * 100))
            score += roe_score * roe_weight

        # 配当利回りスコア (高いほど高得点, 0-10%の範囲)
        div_weight = weights.get("dividend_weight", 0.2)
        dy = metrics.get("dividend_yield")
        if dy is not None and dy > 0:
            div_score = min(100, dy / 10 * 100)
            score += div_score * div_weight

        # モメンタムスコア (52週高値からの距離, 低いほど割安)
        mom_weight = weights.get("momentum_weight", 0.2)
        price = metrics.get("current_price")
        high_52w = metrics.get("52w_high")
        low_52w = metrics.get("52w_low")
        if price and high_52w and low_52w and high_52w > low_52w:
            position = (price - low_52w) / (high_52w - low_52w)
            mom_score = (1 - position) * 100  # 底値に近いほど高得点
            score += mom_score * mom_weight

        return round(score, 2)


def get_engine(
    presets_path: str = "config/screening_presets.yaml",
    exchanges_path: str = "config/exchanges.yaml",
) -> ScreeningEngine:
    """スクリーニングエンジンのファクトリー関数"""
    return ScreeningEngine(presets_path=presets_path, exchanges_path=exchanges_path)
