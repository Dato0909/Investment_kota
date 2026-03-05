"""
銘柄調査・レポート生成モジュール
個別銘柄の詳細財務分析とバリュートラップ判定を行います
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..data.yahoo_client import YahooClient


class ResearchEngine:
    """銘柄調査・分析エンジン"""

    def __init__(self, cache_ttl_hours: float = 24.0):
        self.client = YahooClient(cache_ttl_hours=cache_ttl_hours)

    def analyze_stock(self, ticker: str) -> Dict[str, Any]:
        """
        個別銘柄の詳細分析を実行

        Returns:
            {
                "ticker": ...,
                "metrics": ...,        # 基本財務指標
                "valuation": ...,      # バリュエーション分析
                "health": ...,         # 財務健全性
                "value_trap": ...,     # バリュートラップ判定
                "summary": ...,        # 総合評価
            }
        """
        metrics = self.client.get_screening_metrics(ticker)
        if not metrics:
            return {"error": f"{ticker} のデータを取得できませんでした"}

        valuation = self._analyze_valuation(metrics)
        health = self._analyze_financial_health(metrics)
        value_trap = self._check_value_trap(metrics)
        summary = self._generate_summary(metrics, valuation, health, value_trap)

        return {
            "ticker": ticker,
            "metrics": metrics,
            "valuation": valuation,
            "health": health,
            "value_trap": value_trap,
            "summary": summary,
        }

    def _analyze_valuation(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """バリュエーション分析"""
        per = metrics.get("per")
        pbr = metrics.get("pbr")
        psr = metrics.get("psr")
        ev_ebitda = metrics.get("ev_ebitda")
        dividend_yield = metrics.get("dividend_yield")

        per_rating = _rate_per(per)
        pbr_rating = _rate_pbr(pbr)
        div_rating = _rate_dividend(dividend_yield)

        # 総合バリュエーションスコア (0-100)
        scores = [s for s in [per_rating["score"], pbr_rating["score"], div_rating["score"]] if s is not None]
        overall_score = round(sum(scores) / len(scores), 1) if scores else None

        return {
            "per": {
                "value": per,
                "rating": per_rating["label"],
                "score": per_rating["score"],
                "comment": per_rating["comment"],
            },
            "pbr": {
                "value": pbr,
                "rating": pbr_rating["label"],
                "score": pbr_rating["score"],
                "comment": pbr_rating["comment"],
            },
            "psr": {"value": psr},
            "ev_ebitda": {"value": ev_ebitda},
            "dividend_yield": {
                "value": dividend_yield,
                "rating": div_rating["label"],
                "score": div_rating["score"],
            },
            "overall_score": overall_score,
            "overall_rating": _score_to_label(overall_score),
        }

    def _analyze_financial_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """財務健全性分析"""
        roe = metrics.get("roe")
        roa = metrics.get("roa")
        profit_margin = metrics.get("profit_margin")
        operating_margin = metrics.get("operating_margin")
        current_ratio = metrics.get("current_ratio")
        quick_ratio = metrics.get("quick_ratio")
        debt_to_equity = metrics.get("debt_to_equity")
        revenue_growth = metrics.get("revenue_growth")
        earnings_growth = metrics.get("earnings_growth")

        # 収益性スコア
        profitability_score = _score_profitability(roe, profit_margin, operating_margin)

        # 財務安全性スコア
        safety_score = _score_safety(current_ratio, debt_to_equity)

        # 成長性スコア
        growth_score = _score_growth(revenue_growth, earnings_growth)

        # 総合財務健全性スコア
        scores = [s for s in [profitability_score, safety_score, growth_score] if s is not None]
        overall_score = round(sum(scores) / len(scores), 1) if scores else None

        return {
            "profitability": {
                "roe": roe,
                "roa": roa,
                "profit_margin": profit_margin,
                "operating_margin": operating_margin,
                "score": profitability_score,
                "rating": _score_to_label(profitability_score),
            },
            "safety": {
                "current_ratio": current_ratio,
                "quick_ratio": quick_ratio,
                "debt_to_equity": debt_to_equity,
                "score": safety_score,
                "rating": _score_to_label(safety_score),
            },
            "growth": {
                "revenue_growth": revenue_growth,
                "earnings_growth": earnings_growth,
                "score": growth_score,
                "rating": _score_to_label(growth_score),
            },
            "overall_score": overall_score,
            "overall_rating": _score_to_label(overall_score),
        }

    def _check_value_trap(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        バリュートラップ判定
        低PER・低PBRでも買ってはいけない「罠銘柄」を検出します
        """
        warnings = []
        red_flags = []

        roe = metrics.get("roe")
        revenue_growth = metrics.get("revenue_growth")
        earnings_growth = metrics.get("earnings_growth")
        debt_to_equity = metrics.get("debt_to_equity")
        current_ratio = metrics.get("current_ratio")
        payout_ratio = metrics.get("payout_ratio")
        dividend_yield = metrics.get("dividend_yield")
        profit_margin = metrics.get("profit_margin")

        # ROEが低い (収益性の問題)
        if roe is not None and roe < 5:
            red_flags.append(f"ROEが低い ({roe:.1f}%) — 資本効率が悪い可能性")
        elif roe is not None and roe < 8:
            warnings.append(f"ROEがやや低い ({roe:.1f}%) — 要注意")

        # 売上・利益が減少傾向
        if revenue_growth is not None and revenue_growth < -5:
            red_flags.append(f"売上が減少中 ({revenue_growth:.1f}%) — 事業縮小の懸念")
        elif revenue_growth is not None and revenue_growth < 0:
            warnings.append(f"売上が微減 ({revenue_growth:.1f}%) — トレンドを要確認")

        if earnings_growth is not None and earnings_growth < -10:
            red_flags.append(f"利益が大幅減少中 ({earnings_growth:.1f}%) — 業績悪化")

        # 高負債
        if debt_to_equity is not None and debt_to_equity > 200:
            red_flags.append(f"負債比率が非常に高い (D/E={debt_to_equity:.0f}%) — 財務リスク大")
        elif debt_to_equity is not None and debt_to_equity > 100:
            warnings.append(f"負債比率が高め (D/E={debt_to_equity:.0f}%)")

        # 流動性リスク
        if current_ratio is not None and current_ratio < 1.0:
            red_flags.append(f"流動比率が1未満 ({current_ratio:.2f}) — 短期支払能力に懸念")
        elif current_ratio is not None and current_ratio < 1.5:
            warnings.append(f"流動比率がやや低い ({current_ratio:.2f})")

        # 配当性向が過剰
        if payout_ratio is not None and payout_ratio > 100:
            red_flags.append(f"配当性向100%超 ({payout_ratio:.0f}%) — 配当は持続不可能な可能性")
        elif payout_ratio is not None and payout_ratio > 80:
            warnings.append(f"配当性向が高い ({payout_ratio:.0f}%) — 減配リスクあり")

        # 利益率が極めて低い
        if profit_margin is not None and profit_margin < 1:
            red_flags.append(f"純利益率が非常に低い ({profit_margin:.1f}%) — 収益力に疑問")

        # 判定
        if len(red_flags) >= 3:
            risk_level = "HIGH"
            verdict = "バリュートラップの可能性が高い — 慎重に検討"
        elif len(red_flags) >= 1:
            risk_level = "MEDIUM"
            verdict = "一部のリスク要因あり — 詳細調査を推奨"
        elif len(warnings) >= 2:
            risk_level = "LOW_MEDIUM"
            verdict = "軽微な懸念点あり — 継続的モニタリングを推奨"
        else:
            risk_level = "LOW"
            verdict = "バリュートラップの可能性は低い"

        return {
            "risk_level": risk_level,
            "verdict": verdict,
            "red_flags": red_flags,
            "warnings": warnings,
        }

    def _generate_summary(
        self,
        metrics: Dict[str, Any],
        valuation: Dict[str, Any],
        health: Dict[str, Any],
        value_trap: Dict[str, Any],
    ) -> Dict[str, Any]:
        """総合評価サマリーを生成"""
        val_score = valuation.get("overall_score", 50)
        health_score = health.get("overall_score", 50)
        trap_risk = value_trap.get("risk_level", "MEDIUM")

        # トラップリスクによるペナルティ
        trap_penalty = {"HIGH": 30, "MEDIUM": 15, "LOW_MEDIUM": 5, "LOW": 0}.get(trap_risk, 15)

        # 総合スコア
        if val_score is not None and health_score is not None:
            total_score = max(0, round((val_score * 0.5 + health_score * 0.5) - trap_penalty, 1))
        else:
            total_score = None

        # 投資推奨度
        if total_score is None:
            recommendation = "データ不足"
        elif total_score >= 70:
            recommendation = "Strong Buy (積極的な買い候補)"
        elif total_score >= 55:
            recommendation = "Buy (買い候補)"
        elif total_score >= 40:
            recommendation = "Hold / Watch (様子見)"
        elif total_score >= 25:
            recommendation = "Weak Hold (弱含み)"
        else:
            recommendation = "Avoid (回避推奨)"

        return {
            "ticker": metrics.get("ticker"),
            "name": metrics.get("name"),
            "sector": metrics.get("sector"),
            "valuation_score": val_score,
            "health_score": health_score,
            "trap_risk": trap_risk,
            "total_score": total_score,
            "recommendation": recommendation,
        }

    def compare_stocks(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """複数銘柄を比較分析"""
        results = []
        for ticker in tickers:
            analysis = self.analyze_stock(ticker)
            if "error" not in analysis:
                results.append(analysis["summary"])
        results.sort(key=lambda x: x.get("total_score") or 0, reverse=True)
        return results


# ------------------------------------------------------------------
# スコアリングヘルパー
# ------------------------------------------------------------------

def _rate_per(per: Optional[float]) -> Dict:
    if per is None:
        return {"label": "N/A", "score": None, "comment": "データなし"}
    if per <= 0:
        return {"label": "赤字", "score": 10, "comment": "赤字企業 (要注意)"}
    elif per <= 10:
        return {"label": "超割安", "score": 95, "comment": f"PER {per:.1f}倍 — 非常に割安"}
    elif per <= 15:
        return {"label": "割安", "score": 80, "comment": f"PER {per:.1f}倍 — 割安圏"}
    elif per <= 20:
        return {"label": "適正", "score": 65, "comment": f"PER {per:.1f}倍 — 適正水準"}
    elif per <= 30:
        return {"label": "やや割高", "score": 45, "comment": f"PER {per:.1f}倍 — やや高め"}
    else:
        return {"label": "割高", "score": 20, "comment": f"PER {per:.1f}倍 — 割高圏"}


def _rate_pbr(pbr: Optional[float]) -> Dict:
    if pbr is None:
        return {"label": "N/A", "score": None, "comment": "データなし"}
    if pbr <= 0:
        return {"label": "N/A", "score": None, "comment": "データ異常"}
    elif pbr <= 0.5:
        return {"label": "超割安", "score": 95, "comment": f"PBR {pbr:.2f}倍 — 解散価値以下"}
    elif pbr <= 1.0:
        return {"label": "割安", "score": 80, "comment": f"PBR {pbr:.2f}倍 — 解散価値近辺"}
    elif pbr <= 2.0:
        return {"label": "適正", "score": 65, "comment": f"PBR {pbr:.2f}倍 — 適正水準"}
    elif pbr <= 4.0:
        return {"label": "やや割高", "score": 40, "comment": f"PBR {pbr:.2f}倍 — やや高め"}
    else:
        return {"label": "割高", "score": 20, "comment": f"PBR {pbr:.2f}倍 — 割高圏"}


def _rate_dividend(dy: Optional[float]) -> Dict:
    if dy is None or dy == 0:
        return {"label": "無配", "score": 20}
    elif dy >= 5.0:
        return {"label": "高配当", "score": 85}
    elif dy >= 3.0:
        return {"label": "中配当", "score": 70}
    elif dy >= 1.5:
        return {"label": "低配当", "score": 50}
    else:
        return {"label": "ごく低配当", "score": 30}


def _score_profitability(roe: Optional[float], margin: Optional[float], op_margin: Optional[float]) -> Optional[float]:
    scores = []
    if roe is not None:
        scores.append(min(100, max(0, roe / 25 * 100)))
    if margin is not None:
        scores.append(min(100, max(0, margin / 20 * 100)))
    if op_margin is not None:
        scores.append(min(100, max(0, op_margin / 20 * 100)))
    return round(sum(scores) / len(scores), 1) if scores else None


def _score_safety(current_ratio: Optional[float], de_ratio: Optional[float]) -> Optional[float]:
    scores = []
    if current_ratio is not None:
        if current_ratio >= 2.0:
            scores.append(90)
        elif current_ratio >= 1.5:
            scores.append(70)
        elif current_ratio >= 1.0:
            scores.append(50)
        else:
            scores.append(20)
    if de_ratio is not None:
        if de_ratio <= 30:
            scores.append(90)
        elif de_ratio <= 80:
            scores.append(70)
        elif de_ratio <= 150:
            scores.append(50)
        else:
            scores.append(20)
    return round(sum(scores) / len(scores), 1) if scores else None


def _score_growth(rev_growth: Optional[float], earn_growth: Optional[float]) -> Optional[float]:
    scores = []
    if rev_growth is not None:
        if rev_growth >= 15:
            scores.append(90)
        elif rev_growth >= 5:
            scores.append(70)
        elif rev_growth >= 0:
            scores.append(50)
        else:
            scores.append(20)
    if earn_growth is not None:
        if earn_growth >= 15:
            scores.append(90)
        elif earn_growth >= 5:
            scores.append(70)
        elif earn_growth >= 0:
            scores.append(50)
        else:
            scores.append(20)
    return round(sum(scores) / len(scores), 1) if scores else None


def _score_to_label(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    if score >= 80:
        return "優秀 (Excellent)"
    elif score >= 65:
        return "良好 (Good)"
    elif score >= 50:
        return "普通 (Fair)"
    elif score >= 35:
        return "要注意 (Caution)"
    else:
        return "問題あり (Poor)"
