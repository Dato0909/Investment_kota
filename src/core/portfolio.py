"""
ポートフォリオ管理モジュール
売買記録・損益計算・HHI集中度・リバランス・複利シミュレーションを提供します
"""

from __future__ import annotations

import csv
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


PORTFOLIO_CSV = "data/portfolio.csv"
WATCHLIST_CSV = "data/watchlist.csv"

PORTFOLIO_HEADERS = [
    "id", "ticker", "name", "action", "shares", "price",
    "commission", "date", "note",
]
WATCHLIST_HEADERS = ["ticker", "name", "added_date", "target_price", "note"]


# ===========================================================================
# ポートフォリオ管理
# ===========================================================================

class Portfolio:
    """ポートフォリオ売買記録の管理クラス"""

    def __init__(self, csv_path: str = PORTFOLIO_CSV):
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_csv()

    def _ensure_csv(self) -> None:
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=PORTFOLIO_HEADERS)
                writer.writeheader()

    def _load_records(self) -> List[Dict[str, Any]]:
        records = []
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    **row,
                    "shares": float(row["shares"]) if row.get("shares") else 0.0,
                    "price": float(row["price"]) if row.get("price") else 0.0,
                    "commission": float(row["commission"]) if row.get("commission") else 0.0,
                })
        return records

    def _save_records(self, records: List[Dict[str, Any]]) -> None:
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PORTFOLIO_HEADERS)
            writer.writeheader()
            writer.writerows(records)

    def _next_id(self, records: List[Dict]) -> int:
        if not records:
            return 1
        ids = [int(r.get("id", 0)) for r in records if r.get("id")]
        return max(ids) + 1 if ids else 1

    def add_trade(
        self,
        ticker: str,
        name: str,
        action: str,
        shares: float,
        price: float,
        commission: float = 0.0,
        trade_date: Optional[str] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """売買記録を追加"""
        if action not in ("buy", "sell"):
            return {"error": "action は 'buy' または 'sell' を指定してください"}
        if shares <= 0:
            return {"error": "株数は正の数を指定してください"}
        if price <= 0:
            return {"error": "価格は正の数を指定してください"}

        records = self._load_records()
        record_id = self._next_id(records)
        record = {
            "id": record_id,
            "ticker": ticker.upper(),
            "name": name,
            "action": action,
            "shares": shares,
            "price": price,
            "commission": commission,
            "date": trade_date or str(date.today()),
            "note": note,
        }
        records.append(record)
        self._save_records(records)
        return {"success": True, "record": record}

    def get_holdings(self) -> Dict[str, Dict[str, Any]]:
        """現在の保有銘柄と平均取得価格を計算"""
        records = self._load_records()
        holdings: Dict[str, Dict] = {}

        for r in records:
            ticker = r["ticker"]
            if ticker not in holdings:
                holdings[ticker] = {
                    "ticker": ticker,
                    "name": r.get("name", ticker),
                    "total_shares": 0.0,
                    "total_cost": 0.0,
                    "total_commission": 0.0,
                    "trades": [],
                }
            h = holdings[ticker]
            shares = r["shares"]
            price = r["price"]
            commission = r["commission"]

            if r["action"] == "buy":
                h["total_shares"] += shares
                h["total_cost"] += shares * price + commission
                h["total_commission"] += commission
            elif r["action"] == "sell":
                h["total_shares"] -= shares
                h["total_cost"] -= shares * h.get("avg_cost", price)
                h["total_commission"] += commission

            h["trades"].append(r)

        # 保有ゼロの銘柄を除外し、平均取得価格を計算
        active = {}
        for ticker, h in holdings.items():
            if h["total_shares"] > 0.001:
                h["avg_cost"] = h["total_cost"] / h["total_shares"]
                active[ticker] = h

        return active

    def calculate_pnl(self, current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """現在株価を使って損益を計算"""
        holdings = self.get_holdings()
        results = []

        for ticker, h in holdings.items():
            current_price = current_prices.get(ticker)
            if current_price is None:
                results.append({
                    **h,
                    "current_price": None,
                    "market_value": None,
                    "unrealized_pnl": None,
                    "unrealized_pnl_pct": None,
                })
                continue

            avg_cost = h["avg_cost"]
            shares = h["total_shares"]
            market_value = shares * current_price
            cost_basis = shares * avg_cost
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0

            results.append({
                **h,
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "cost_basis": round(cost_basis, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
            })

        results.sort(key=lambda x: (x.get("market_value") or 0), reverse=True)
        return results

    def get_summary(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """ポートフォリオサマリーを計算"""
        pnl_data = self.calculate_pnl(current_prices)

        total_market_value = sum(
            r["market_value"] or 0 for r in pnl_data
        )
        total_cost = sum(
            r.get("cost_basis") or 0 for r in pnl_data
        )
        total_unrealized_pnl = sum(
            r.get("unrealized_pnl") or 0 for r in pnl_data
        )

        # HHI 集中度指数
        hhi = self._calculate_hhi(pnl_data, total_market_value)

        # アセットアロケーション
        allocation = []
        for r in pnl_data:
            mv = r.get("market_value") or 0
            weight = (mv / total_market_value * 100) if total_market_value > 0 else 0
            allocation.append({
                "ticker": r["ticker"],
                "name": r.get("name", r["ticker"]),
                "market_value": r["market_value"],
                "weight_pct": round(weight, 2),
                "unrealized_pnl_pct": r.get("unrealized_pnl_pct"),
            })

        return {
            "holdings_count": len(pnl_data),
            "total_market_value": round(total_market_value, 2),
            "total_cost_basis": round(total_cost, 2),
            "total_unrealized_pnl": round(total_unrealized_pnl, 2),
            "total_return_pct": round(
                (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0, 2
            ),
            "hhi": round(hhi, 4),
            "hhi_risk": _hhi_risk_label(hhi),
            "allocation": allocation,
            "holdings": pnl_data,
        }

    def _calculate_hhi(self, holdings: List[Dict], total_value: float) -> float:
        """
        Herfindahl-Hirschman Index (集中度指数) を計算
        HHI = Σ(各銘柄の比率²) → 0: 完全分散, 1: 完全集中
        """
        if total_value <= 0 or not holdings:
            return 0.0
        hhi = sum(
            ((h.get("market_value") or 0) / total_value) ** 2
            for h in holdings
        )
        return hhi

    def rebalance_suggestions(
        self,
        current_prices: Dict[str, float],
        target_weights: Optional[Dict[str, float]] = None,
        equal_weight: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        リバランス提案を生成
        target_weights: {ticker: weight (0-1)} または equal_weight=True で均等配分
        """
        holdings = self.get_holdings()
        if not holdings:
            return []

        summary = self.get_summary(current_prices)
        total_value = summary["total_market_value"]

        if equal_weight:
            n = len(holdings)
            target_weights = {ticker: 1.0 / n for ticker in holdings}

        if not target_weights:
            return []

        suggestions = []
        for ticker, target_w in target_weights.items():
            h = holdings.get(ticker, {})
            current_price = current_prices.get(ticker, 0)
            if not current_price:
                continue

            current_value = (h.get("total_shares", 0) * current_price)
            target_value = total_value * target_w
            diff_value = target_value - current_value
            diff_shares = diff_value / current_price if current_price > 0 else 0

            suggestions.append({
                "ticker": ticker,
                "current_weight_pct": round(current_value / total_value * 100, 2) if total_value > 0 else 0,
                "target_weight_pct": round(target_w * 100, 2),
                "diff_value": round(diff_value, 2),
                "diff_shares": round(diff_shares, 4),
                "action": "buy" if diff_value > 0 else "sell" if diff_value < 0 else "hold",
            })

        suggestions.sort(key=lambda x: abs(x["diff_value"]), reverse=True)
        return suggestions

    def compound_simulation(
        self,
        initial_investment: float,
        annual_return_pct: float,
        annual_dividend_pct: float = 0.0,
        years: int = 20,
        monthly_contribution: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        複利シミュレーション
        Args:
            initial_investment: 初期投資額
            annual_return_pct: 年間リターン率 (%)
            annual_dividend_pct: 年間配当利回り (%)
            years: シミュレーション年数
            monthly_contribution: 毎月積立額
        """
        r = annual_return_pct / 100
        d = annual_dividend_pct / 100
        total_r = r + d

        results = []
        value = initial_investment
        total_invested = initial_investment

        for year in range(1, years + 1):
            dividend_received = value * d
            value = value * (1 + r) + monthly_contribution * 12
            total_invested += monthly_contribution * 12
            results.append({
                "year": year,
                "portfolio_value": round(value, 0),
                "total_invested": round(total_invested, 0),
                "total_gain": round(value - total_invested, 0),
                "dividend_received_annual": round(dividend_received, 0),
                "return_pct": round((value - total_invested) / total_invested * 100, 2),
            })

        return results

    def get_all_records(self) -> List[Dict[str, Any]]:
        """全売買記録を返す"""
        return self._load_records()

    def delete_record(self, record_id: int) -> bool:
        """売買記録を削除"""
        records = self._load_records()
        new_records = [r for r in records if str(r.get("id")) != str(record_id)]
        if len(new_records) == len(records):
            return False
        self._save_records(new_records)
        return True


# ===========================================================================
# ウォッチリスト管理
# ===========================================================================

class Watchlist:
    """ウォッチリスト管理クラス"""

    def __init__(self, csv_path: str = WATCHLIST_CSV):
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_csv()

    def _ensure_csv(self) -> None:
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=WATCHLIST_HEADERS)
                writer.writeheader()

    def _load(self) -> List[Dict[str, str]]:
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _save(self, records: List[Dict[str, str]]) -> None:
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=WATCHLIST_HEADERS)
            writer.writeheader()
            writer.writerows(records)

    def add(self, ticker: str, name: str = "", target_price: float = 0.0, note: str = "") -> Dict:
        """ウォッチリストに銘柄を追加"""
        records = self._load()
        tickers = [r["ticker"].upper() for r in records]
        ticker = ticker.upper()

        if ticker in tickers:
            return {"error": f"{ticker} はすでにウォッチリストにあります"}

        record = {
            "ticker": ticker,
            "name": name or ticker,
            "added_date": str(date.today()),
            "target_price": str(target_price) if target_price else "",
            "note": note,
        }
        records.append(record)
        self._save(records)
        return {"success": True, "record": record}

    def remove(self, ticker: str) -> bool:
        """ウォッチリストから銘柄を削除"""
        records = self._load()
        new_records = [r for r in records if r["ticker"].upper() != ticker.upper()]
        if len(new_records) == len(records):
            return False
        self._save(new_records)
        return True

    def get_all(self) -> List[Dict[str, str]]:
        """ウォッチリスト全件を返す"""
        return self._load()

    def get_tickers(self) -> List[str]:
        """ティッカーリストのみ返す"""
        return [r["ticker"] for r in self._load()]


# ===========================================================================
# ユーティリティ
# ===========================================================================

def _hhi_risk_label(hhi: float) -> str:
    """HHI値からリスクラベルを返す"""
    if hhi < 0.1:
        return "低リスク (十分に分散)"
    elif hhi < 0.18:
        return "中リスク (やや集中)"
    elif hhi < 0.25:
        return "高リスク (集中傾向)"
    else:
        return "非常に高いリスク (過度に集中)"
