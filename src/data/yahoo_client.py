"""
Yahoo Finance APIクライアント
yfinanceを使って株価・財務データを取得し、24時間JSONキャッシュで管理します
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import yfinance as yf

from .cache import Cache


class YahooClient:
    """Yahoo Finance APIのラッパークライアント（キャッシュ付き）"""

    def __init__(self, cache_ttl_hours: float = 24.0, cache_dir: str = "data/cache"):
        self.cache = Cache(cache_dir=cache_dir, ttl_hours=cache_ttl_hours)

    # ------------------------------------------------------------------
    # 基本情報取得
    # ------------------------------------------------------------------

    def get_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """銘柄の基本情報・財務指標を取得"""
        cache_key = f"info_{ticker}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
                return None
            result = dict(info)
            self.cache.set(cache_key, result)
            return result
        except Exception:
            return None

    def get_price(self, ticker: str) -> Optional[float]:
        """現在株価を取得"""
        info = self.get_info(ticker)
        if not info:
            return None
        return info.get("currentPrice") or info.get("regularMarketPrice")

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> Optional[List[Dict]]:
        """株価履歴を取得 (リスト形式で返す)"""
        cache_key = f"history_{ticker}_{period}_{interval}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
            if hist.empty:
                return None

            result = []
            for idx, row in hist.iterrows():
                result.append({
                    "date": str(idx.date()),
                    "open": float(row["Open"]) if not _is_nan(row["Open"]) else None,
                    "high": float(row["High"]) if not _is_nan(row["High"]) else None,
                    "low": float(row["Low"]) if not _is_nan(row["Low"]) else None,
                    "close": float(row["Close"]) if not _is_nan(row["Close"]) else None,
                    "volume": int(row["Volume"]) if not _is_nan(row["Volume"]) else None,
                })
            self.cache.set(cache_key, result)
            return result
        except Exception:
            return None

    def get_financials(self, ticker: str) -> Optional[Dict[str, Any]]:
        """財務諸表データを取得 (損益計算書・貸借対照表・CF計算書)"""
        cache_key = f"financials_{ticker}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            stock = yf.Ticker(ticker)
            result = {}

            # 損益計算書
            if not stock.financials.empty:
                result["income_statement"] = _df_to_dict(stock.financials)

            # 貸借対照表
            if not stock.balance_sheet.empty:
                result["balance_sheet"] = _df_to_dict(stock.balance_sheet)

            # キャッシュフロー計算書
            if not stock.cashflow.empty:
                result["cashflow"] = _df_to_dict(stock.cashflow)

            if result:
                self.cache.set(cache_key, result)
                return result
            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # スクリーニング用のキーメトリクス取得
    # ------------------------------------------------------------------

    def get_screening_metrics(self, ticker: str) -> Optional[Dict[str, Any]]:
        """スクリーニング用の主要財務指標をまとめて取得"""
        info = self.get_info(ticker)
        if not info:
            return None

        def safe_float(key: str) -> Optional[float]:
            val = info.get(key)
            if val is None or _is_nan(val):
                return None
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        market_cap = safe_float("marketCap")

        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            # バリュエーション
            "per": safe_float("trailingPE") or safe_float("forwardPE"),
            "pbr": safe_float("priceToBook"),
            "psr": safe_float("priceToSalesTrailing12Months"),
            "ev_ebitda": safe_float("enterpriseToEbitda"),
            # 収益性
            "roe": _pct(safe_float("returnOnEquity")),
            "roa": _pct(safe_float("returnOnAssets")),
            "profit_margin": _pct(safe_float("profitMargins")),
            "operating_margin": _pct(safe_float("operatingMargins")),
            "gross_margin": _pct(safe_float("grossMargins")),
            # 配当
            "dividend_yield": _pct(safe_float("dividendYield")),
            "payout_ratio": _pct(safe_float("payoutRatio")),
            # 成長
            "revenue_growth": _pct(safe_float("revenueGrowth")),
            "earnings_growth": _pct(safe_float("earningsGrowth")),
            # 財務健全性
            "debt_to_equity": safe_float("debtToEquity"),
            "current_ratio": safe_float("currentRatio"),
            "quick_ratio": safe_float("quickRatio"),
            # 規模
            "market_cap": market_cap,
            "market_cap_billion": round(market_cap / 1e9, 2) if market_cap else None,
            "enterprise_value": safe_float("enterpriseValue"),
            # 株価
            "current_price": safe_float("currentPrice") or safe_float("regularMarketPrice"),
            "52w_high": safe_float("fiftyTwoWeekHigh"),
            "52w_low": safe_float("fiftyTwoWeekLow"),
            "beta": safe_float("beta"),
            # 出来高
            "avg_volume": safe_float("averageVolume"),
        }

    def get_multiple_metrics(self, tickers: List[str], delay: float = 0.3) -> List[Dict[str, Any]]:
        """複数銘柄の指標を一括取得。失敗した銘柄はスキップ"""
        results = []
        for ticker in tickers:
            metrics = self.get_screening_metrics(ticker)
            if metrics:
                results.append(metrics)
            if delay > 0:
                time.sleep(delay)
        return results


# ------------------------------------------------------------------
# ユーティリティ関数
# ------------------------------------------------------------------

def _is_nan(val: Any) -> bool:
    """NaN/Noneチェック"""
    if val is None:
        return True
    try:
        import math
        return math.isnan(float(val))
    except (TypeError, ValueError):
        return False


def _pct(val: Optional[float]) -> Optional[float]:
    """小数の比率をパーセント表示用に変換 (0.05 → 5.0)"""
    if val is None:
        return None
    if abs(val) <= 1.0:
        return round(val * 100, 2)
    return round(val, 2)


def _df_to_dict(df) -> Dict[str, Any]:
    """DataFrameをJSONシリアライズ可能な辞書に変換"""
    result = {}
    for col in df.columns:
        col_str = str(col.date()) if hasattr(col, "date") else str(col)
        result[col_str] = {}
        for idx in df.index:
            val = df.loc[idx, col]
            if _is_nan(val):
                result[col_str][str(idx)] = None
            else:
                try:
                    result[col_str][str(idx)] = float(val)
                except (TypeError, ValueError):
                    result[col_str][str(idx)] = str(val)
    return result
