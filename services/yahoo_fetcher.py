import requests
from typing import Dict, Any, List, Optional


class YahooFetcher:
    def __init__(self):
        self.autocomplete_url = "https://autoc.finance.yahoo.com/autoc"
        self.search_url = "https://query1.finance.yahoo.com/v1/finance/search"

    def resolve_ticker(self, company_query: str) -> Optional[Dict[str, Any]]:
        try:
            params = {"query": company_query, "region": 1, "lang": "en"}
            resp = requests.get(self.autocomplete_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("ResultSet", {}).get("Result", []):
                if item.get("typeDisp") in ("Equity", "Equity ETF", "ETF"):
                    return {
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "exch": item.get("exchDisp"),
                        "type": item.get("typeDisp"),
                    }
            return None
        except Exception:
            return None

    def search_news(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        try:
            params = {"q": query, "quotesCount": 0, "newsCount": count, "listsCount": 0}
            resp = requests.get(self.search_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            news_items = []
            for item in data.get("news", [])[:count]:
                news_items.append({
                    "title": item.get("title"),
                    "publisher": item.get("publisher"),
                    "link": item.get("link"),
                    "published": item.get("providerPublishTime"),
                    "type": item.get("type"),
                })
            return news_items
        except Exception:
            return []


