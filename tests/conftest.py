"""
pytest conftest.py
yfinanceをモック化して、API呼び出しなしにテストを実行します
"""

import sys
from unittest.mock import MagicMock, patch


# yfinanceが利用できない場合のモック
class MockYFinance:
    """yfinanceのモッククラス"""

    class Ticker:
        def __init__(self, ticker):
            self.ticker = ticker
            self._info = {
                "longName": f"Test Corp ({ticker})",
                "shortName": ticker,
                "sector": "Technology",
                "industry": "Software",
                "country": "Japan",
                "currency": "JPY",
                "currentPrice": 2500.0,
                "regularMarketPrice": 2500.0,
                "marketCap": 300_000_000_000,
                "trailingPE": 12.0,
                "priceToBook": 1.2,
                "returnOnEquity": 0.15,
                "returnOnAssets": 0.08,
                "profitMargins": 0.10,
                "operatingMargins": 0.12,
                "grossMargins": 0.35,
                "dividendYield": 0.035,
                "payoutRatio": 0.35,
                "revenueGrowth": 0.05,
                "earningsGrowth": 0.08,
                "debtToEquity": 80.0,
                "currentRatio": 1.8,
                "quickRatio": 1.2,
                "beta": 0.9,
                "fiftyTwoWeekHigh": 3000.0,
                "fiftyTwoWeekLow": 2000.0,
                "averageVolume": 1_000_000,
                "enterpriseToEbitda": 8.0,
                "priceToSalesTrailing12Months": 0.8,
                "enterpriseValue": 350_000_000_000,
            }

        @property
        def info(self):
            return self._info

        @property
        def financials(self):
            import pandas as pd
            return pd.DataFrame()

        @property
        def balance_sheet(self):
            import pandas as pd
            return pd.DataFrame()

        @property
        def cashflow(self):
            import pandas as pd
            return pd.DataFrame()

        def history(self, period="1y", interval="1d"):
            import pandas as pd
            import numpy as np
            dates = pd.date_range(end=pd.Timestamp.now(), periods=5)
            return pd.DataFrame({
                "Open": [2400, 2450, 2500, 2480, 2510],
                "High": [2450, 2500, 2550, 2530, 2560],
                "Low": [2380, 2430, 2470, 2450, 2490],
                "Close": [2430, 2490, 2520, 2480, 2500],
                "Volume": [1000000, 1200000, 900000, 1100000, 950000],
            }, index=dates)


# yfinanceをモックとして登録
try:
    import yfinance
except ImportError:
    sys.modules["yfinance"] = MockYFinance()
