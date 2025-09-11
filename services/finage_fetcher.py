import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

class FinageFetcher:
    def __init__(self):
        self.api_key = os.getenv("FINAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Finage API key not found in environment variables")
        
        self.base_url = "https://api.finage.co.uk"
        self.session = requests.Session()
        self.session.params = {"apikey": self.api_key}
    
    def get_stock_quote(self, ticker: str) -> Dict[str, Any]:
        """Get latest stock quote with price and daily change."""
        try:
            url = f"{self.base_url}/last/stock/{ticker}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get previous close for change calculation
            prev_close_data = self._get_previous_close(ticker)
            
            quote_data = {
                "ticker": ticker.upper(),
                "price": data.get("price", 0),
                "timestamp": data.get("timestamp"),
                "previous_close": prev_close_data.get("close", data.get("price", 0)),
                "change": 0,
                "change_percent": 0,
                "volume": data.get("volume", 0)
            }
            
            # Calculate change
            if quote_data["previous_close"] > 0:
                quote_data["change"] = quote_data["price"] - quote_data["previous_close"]
                quote_data["change_percent"] = (quote_data["change"] / quote_data["previous_close"]) * 100
            
            return quote_data
            
        except requests.exceptions.RequestException as e:
            return {
                "ticker": ticker.upper(),
                "price": 0,
                "error": f"Failed to fetch quote: {str(e)}"
            }
    
    def _get_previous_close(self, ticker: str) -> Dict[str, Any]:
        """Get previous trading day's close price."""
        try:
            # Get last 2 days of data to find previous close
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Get a week to ensure we have data
            
            url = f"{self.base_url}/agg/stock/prev-close/{ticker}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                "close": data.get("c", 0),
                "date": data.get("t")
            }
            
        except Exception:
            return {"close": 0}
    
    def get_stock_history(self, ticker: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """Get historical OHLC prices."""
        try:
            url = f"{self.base_url}/agg/stock/{ticker}/1/day/{from_date}/{to_date}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "results" not in data:
                return []
            
            history = []
            for item in data["results"]:
                history.append({
                    "date": datetime.fromtimestamp(item["t"] / 1000).strftime("%Y-%m-%d"),
                    "open": item.get("o", 0),
                    "high": item.get("h", 0),
                    "low": item.get("l", 0),
                    "close": item.get("c", 0),
                    "volume": item.get("v", 0)
                })
            
            return sorted(history, key=lambda x: x["date"])
            
        except requests.exceptions.RequestException as e:
            return []
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """Get company fundamentals and information."""
        try:
            # Get company details
            url = f"{self.base_url}/detail/stock/{ticker}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            company_info = {
                "ticker": ticker.upper(),
                "name": data.get("name", "N/A"),
                "sector": data.get("sector", "N/A"),
                "industry": data.get("industry", "N/A"),
                "market_cap": data.get("marketCap", "N/A"),
                "pe_ratio": data.get("peRatio", "N/A"),
                "dividend_yield": data.get("dividendYield", "N/A"),
                "beta": data.get("beta", "N/A"),
                "description": data.get("description", "N/A")
            }
            
            return company_info
            
        except requests.exceptions.RequestException as e:
            return {
                "ticker": ticker.upper(),
                "name": "N/A",
                "error": f"Failed to fetch company info: {str(e)}"
            }
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status."""
        try:
            url = f"{self.base_url}/market/status"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return {
                "is_open": data.get("isOpen", False),
                "market": data.get("market", "US"),
                "session": data.get("session", "unknown")
            }
            
        except Exception:
            return {"is_open": False, "market": "US", "session": "unknown"}