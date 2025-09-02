from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import os
from typing import Dict, Any

from backend.database import DatabaseManager
from backend.ai_pipeline import FinancialAIPipeline
from backend.pdf_generator import PDFReportGenerator
from services.finage_fetcher import FinageFetcher

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Financial AI Assistant", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_manager = DatabaseManager()
ai_pipeline = FinancialAIPipeline()
pdf_generator = PDFReportGenerator()
finage_fetcher = FinageFetcher()

# Request models
class InvestmentQuery(BaseModel):
    ticker: str
    question: str

class HealthResponse(BaseModel):
    status: str
    message: str

class StockDataResponse(BaseModel):
    ticker: str
    quote: Dict[str, Any]
    company_info: Dict[str, Any]
    market_status: Dict[str, Any]

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(status="healthy", message="Financial AI Assistant API is running")

@app.get("/data/quote/{ticker}")
async def get_stock_quote(ticker: str) -> Dict[str, Any]:
    """Get real-time stock quote."""
    try:
        quote = finage_fetcher.get_stock_quote(ticker.upper())
        company_info = finage_fetcher.get_company_info(ticker.upper())
        market_status = finage_fetcher.get_market_status()
        
        return {
            "ticker": ticker.upper(),
            "quote": quote,
            "company_info": company_info,
            "market_status": market_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock data: {str(e)}")

@app.get("/data/history/{ticker}")
async def get_stock_history(ticker: str, days: int = 30) -> Dict[str, Any]:
    """Get historical stock data."""
    try:
        from datetime import datetime, timedelta
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        history = finage_fetcher.get_stock_history(ticker.upper(), start_date, end_date)
        
        return {
            "ticker": ticker.upper(),
            "history": history,
            "period": f"{days} days"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")

@app.post("/ask")
async def ask_investment_question(query: InvestmentQuery) -> Dict[str, Any]:
    """Process investment question and return AI-generated answer."""
    try:
        # Validate input
        if not query.ticker or not query.question:
            raise HTTPException(status_code=400, detail="Both ticker and question are required")
        
        # Process query through AI pipeline
        result = ai_pipeline.analyze_investment_query(query.ticker.upper(), query.question)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "AI processing failed"))
        
        # Save to database
        db_manager.save_query(
            ticker=query.ticker.upper(),
            question=query.question,
            answer=result["answer"],
            stock_data=json.dumps(result.get("stock_data", {})),
            company_info=json.dumps(result.get("company_info", {}))
        )
        
        return {
            "ticker": query.ticker.upper(),
            "question": query.question,
            "answer": result["answer"],
            "stock_data": result.get("stock_data", {}),
            "company_info": result.get("company_info", {}),
            "historical_data": result.get("historical_data", []),
            "context_sources": result.get("sources", []),
            "timestamp": "now"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/reports/stock")
async def generate_stock_report(query: InvestmentQuery):
    """Generate and return a PDF investment report."""
    try:
        # Validate input
        if not query.ticker or not query.question:
            raise HTTPException(status_code=400, detail="Both ticker and question are required")
        
        # Generate detailed report content
        report_data = ai_pipeline.generate_detailed_report(query.ticker.upper(), query.question)
        
        if not report_data["success"]:
            raise HTTPException(status_code=500, detail=report_data.get("error", "Report generation failed"))
        
        # Generate PDF
        pdf_path = pdf_generator.generate_investment_report(report_data)
        
        # Save query to database
        db_manager.save_query(
            ticker=query.ticker.upper(),
            question=query.question,
            answer=f"PDF Report generated: {os.path.basename(pdf_path)}",
            stock_data=json.dumps(report_data.get("stock_data", {})),
            company_info=json.dumps(report_data.get("company_info", {}))
        )
        
        # Return PDF file
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=os.path.basename(pdf_path)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

@app.get("/history")
async def get_query_history(limit: int = 10) -> Dict[str, Any]:
    """Get recent query history."""
    try:
        queries = db_manager.get_recent_queries(limit)
        return {
            "queries": queries,
            "total": len(queries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/history/{ticker}")
async def get_ticker_history(ticker: str) -> Dict[str, Any]:
    """Get query history for specific ticker."""
    try:
        queries = db_manager.get_queries_by_ticker(ticker.upper())
        return {
            "ticker": ticker.upper(),
            "queries": queries,
            "total": len(queries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)