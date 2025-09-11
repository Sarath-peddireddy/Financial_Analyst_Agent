import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.vector_store import VectorStore
from services.finage_fetcher import FinageFetcher
from services.yahoo_fetcher import YahooFetcher
import json

class FinancialAIPipeline:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-0125")
        self.llm = ChatOpenAI(model=model_name, temperature=0.1, api_key=self.openai_api_key)
        self.vector_store = VectorStore()
        self.finage = FinageFetcher()
        self.yahoo = YahooFetcher()
    
    def analyze_investment_query(self, company_or_ticker: str, question: str) -> Dict[str, Any]:
        """Process investment query using RAG pipeline."""
        try:
            resolved = self.yahoo.resolve_ticker(company_or_ticker)
            ticker = (resolved or {}).get("symbol", company_or_ticker).upper()

            from concurrent.futures import ThreadPoolExecutor
            def fetch_quote():
                return self.finage.get_stock_quote(ticker)
            def fetch_company():
                return self.finage.get_company_info(ticker)
            def fetch_history():
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                return self.finage.get_stock_history(ticker, start_date, end_date)
            def fetch_news():
                return self.yahoo.search_news(resolved.get("name", ticker) if resolved else ticker, count=5)

            with ThreadPoolExecutor(max_workers=4) as executor:
                quote_f = executor.submit(fetch_quote)
                company_f = executor.submit(fetch_company)
                history_f = executor.submit(fetch_history)
                news_f = executor.submit(fetch_news)
                stock_quote = quote_f.result()
                company_info = company_f.result()
                historical_data = history_f.result()
                news = news_f.result()

            search_query = f"{ticker} {question}"
            relevant_docs = self.vector_store.search(search_query, k=3)
            
            context = self._prepare_enhanced_context(relevant_docs, stock_quote, company_info, historical_data)
            if news:
                context += "\n\nLatest News Headlines:\n" + "\n".join([f"- {n['title']} ({n.get('publisher','')})" for n in news])
            
            response = self._generate_response(ticker, question, context)
            risk_score = self._compute_risk_score(company_info, historical_data)
            
            return {
                "success": True,
                "answer": response,
                "stock_data": stock_quote,
                "company_info": company_info,
                "historical_data": historical_data[-5:] if historical_data else [],
                "context_used": len(relevant_docs),
                "sources": [doc["metadata"] for doc in relevant_docs],
                "risk_score": risk_score,
                "news": news,
                "resolved": resolved
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "answer": "I apologize, but I encountered an error processing your request."
            }
    
    def _prepare_enhanced_context(self, docs: List[Dict[str, Any]], stock_quote: Dict[str, Any], 
                                company_info: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> str:
        """Prepare enhanced context with real-time data and retrieved documents."""
        context_parts = []
        
        # Add real-time stock information
        if not stock_quote.get("error"):
            price_info = f"""
Current Stock Information for {stock_quote['ticker']}:
- Current Price: ${stock_quote['price']:.2f}
- Daily Change: ${stock_quote['change']:.2f} ({stock_quote['change_percent']:.2f}%)
- Volume: {stock_quote.get('volume', 'N/A')}
"""
            context_parts.append(price_info)
        
        # Add company information
        if not company_info.get("error"):
            company_details = f"""
Company Information:
- Name: {company_info['name']}
- Sector: {company_info['sector']}
- Industry: {company_info['industry']}
- Market Cap: {company_info.get('market_cap', 'N/A')}
- P/E Ratio: {company_info.get('pe_ratio', 'N/A')}
- Beta: {company_info.get('beta', 'N/A')}
"""
            context_parts.append(company_details)
        
        # Add recent performance data
        if historical_data:
            recent_data = historical_data[-5:]  # Last 5 days
            performance_info = f"""
Recent Performance (Last 5 Trading Days):
"""
            for day in recent_data:
                performance_info += f"- {day['date']}: Close ${day['close']:.2f}, Volume {day['volume']}\n"
            context_parts.append(performance_info)
        
        # Add retrieved documents context
        if docs:
            context_parts.append("\nRelevant Financial Analysis:")
            for i, doc in enumerate(docs, 1):
                context_parts.append(f"Source {i}: {doc['content']}")
        
        return "\n\n".join(context_parts)
    
    def _prepare_context(self, docs: List[Dict[str, Any]]) -> str:
        """Prepare context string from retrieved documents."""
        if not docs:
            return "No specific context available for this query."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"Context {i}: {doc['content']}")
        
        return "\n\n".join(context_parts)
    
    def _generate_response(self, ticker: str, question: str, context: str) -> str:
        """Generate response using OpenAI via LangChain."""
        system_prompt = """You are a professional financial advisor and investment analyst with access to real-time market data. 
        Provide clear, well-reasoned investment advice based on the given context and your knowledge.
        
        Guidelines:
        - Incorporate the real-time stock data and company fundamentals in your analysis
        - Reference current price movements and recent performance trends
        - Be objective and balanced in your analysis
        - Consider both risks and opportunities
        - Provide specific reasoning for your recommendations
        - Include relevant financial metrics when applicable
        - Acknowledge limitations and suggest further research when appropriate
        - Keep responses concise but comprehensive (200-400 words)
        
        IMPORTANT: This is for educational purposes only and not personalized financial advice."""
        
        human_prompt = f"""Based on the real-time data and context about {ticker}, please answer this question: {question}

        Context:
        {context}
        
        Please provide a detailed analysis and recommendation that incorporates the current market data."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = self.llm(messages)
        return response.content

    def _compute_risk_score(self, company_info: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> int:
        try:
            beta = company_info.get("beta") if isinstance(company_info, dict) else None
            beta_val = float(beta) if beta not in (None, "N/A", "") else 1.0
        except Exception:
            beta_val = 1.0
        closes = [d.get("close", 0) for d in (historical_data or []) if isinstance(d.get("close", None), (int, float))]
        vol_component = 0
        if len(closes) >= 5:
            import numpy as np
            returns = np.diff(closes) / np.array(closes[:-1])
            vol = float(np.std(returns)) if returns.size > 0 else 0.0
            vol_component = min(max(vol * 100, 0), 10)
        beta_component = min(max((beta_val - 1.0) * 5 + 5, 0), 10)
        score = int(round(min(max(beta_component + vol_component, 0), 10)))
        return score
    
    def generate_detailed_report(self, company_or_ticker: str, question: str) -> Dict[str, Any]:
        """Generate a more detailed analysis for PDF report."""
        try:
            resolved = self.yahoo.resolve_ticker(company_or_ticker)
            ticker = (resolved or {}).get("symbol", company_or_ticker).upper()

            from concurrent.futures import ThreadPoolExecutor
            def fetch_quote():
                return self.finage.get_stock_quote(ticker)
            def fetch_company():
                return self.finage.get_company_info(ticker)
            def fetch_history():
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                return self.finage.get_stock_history(ticker, start_date, end_date)
            def fetch_news():
                return self.yahoo.search_news(resolved.get("name", ticker) if resolved else ticker, count=7)

            with ThreadPoolExecutor(max_workers=4) as executor:
                quote_f = executor.submit(fetch_quote)
                company_f = executor.submit(fetch_company)
                history_f = executor.submit(fetch_history)
                news_f = executor.submit(fetch_news)
                stock_quote = quote_f.result()
                company_info = company_f.result()
                historical_data = history_f.result()
                news = news_f.result()
            
            # Get comprehensive analysis
            search_query = f"{ticker} financial analysis investment outlook"
            relevant_docs = self.vector_store.search(search_query, k=5)
            context = self._prepare_enhanced_context(relevant_docs, stock_quote, company_info, historical_data)
            if news:
                context += "\n\nLatest News Headlines:\n" + "\n".join([f"- {n['title']} ({n.get('publisher','')})" for n in news])
            
            # Generate detailed report content
            system_prompt = """You are a senior financial analyst preparing a comprehensive investment report with access to real-time market data.
            Provide a detailed, structured analysis suitable for a professional investment report.
            
            Structure your response with:
            1. Executive Summary
            2. Current Market Position (use real-time data)
            3. Company Overview & Fundamentals
            4. Technical Analysis (based on recent price movements)
            5. Risk Assessment
            6. Investment Recommendation
            7. Key Considerations
            
            Make it detailed and professional (600-1000 words). Incorporate the real-time stock data throughout your analysis."""
            

            human_prompt = f"""Prepare a comprehensive investment analysis report for {ticker} addressing: {question}
            Real-time Data and Context:
            {context}"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm(messages)
            risk_score = self._compute_risk_score(company_info, historical_data)
            
            return {
                "success": True,
                "report_content": response.content,
                "ticker": ticker,
                "question": question,
                "stock_data": stock_quote,
                "company_info": company_info,
                "historical_data": historical_data,
                "sources": [doc["metadata"] for doc in relevant_docs],
                "risk_score": risk_score,
                "news": news,
                "resolved": resolved
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "report_content": "Error generating report."
            }
