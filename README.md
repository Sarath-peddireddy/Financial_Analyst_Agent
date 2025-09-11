# Financial AI Assistant

A full-stack application that provides AI-powered investment analysis using FastAPI, FAISS vector search, Finage real-time market data, and OpenAI's GPT models.

## Features

- **Real-time Market Data**: Live stock quotes, company fundamentals, and historical charts via Finage API
- **AI-Powered Analysis**: Get intelligent investment insights for any stock ticker
- **Interactive Charts**: 30-day price performance visualization with Chart.js
- **Vector Search**: FAISS-powered retrieval of relevant financial context
- **PDF Reports**: Generate comprehensive investment analysis reports
- **Query History**: Track and review previous analyses
- **Responsive UI**: Clean, modern interface that works on all devices

## Architecture

### Backend (FastAPI)
- **FastAPI**: REST API with automatic documentation
- **SQLite**: Lightweight database for query storage
- **Finage API**: Real-time stock market data integration
- **FAISS**: Vector similarity search for financial documents
- **LangChain**: AI pipeline orchestration
- **OpenAI**: GPT-3.5-turbo for analysis generation
- **Matplotlib**: Chart generation for PDF reports
- **ReportLab**: PDF report generation

### Frontend (Vanilla JS)
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with gradients and animations
- **JavaScript**: Fetch API for backend communication
- **Chart.js**: Interactive price charts
- **Font Awesome**: Professional icons

## Setup Instructions

### 1. Environment Setup

Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_actual_openai_api_key_here
FINAGE_API_KEY=your_actual_finage_api_key_here
```

### Get API Keys

1. **OpenAI API Key**: 
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key

2. **Finage API Key**:
   - Visit [Finage](https://finage.co.uk/)
   - Sign up for a free account
   - Get your API key from the dashboard

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Backend

```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`
- API Documentation: `http://127.0.0.1:8000/docs`
- Alternative docs: `http://127.0.0.1:8000/redoc`

### 4. Serve the Frontend

Open `frontend/index.html` in your browser, or use a simple HTTP server:

```bash
cd frontend
python -m http.server 3000
```

Then visit `http://localhost:3000`

## API Endpoints

### GET `/data/quote/{ticker}`
Get real-time stock quote and company information.

**Response:**
```json
{
  "ticker": "AAPL",
  "quote": {
    "price": 150.25,
    "change": 2.50,
    "change_percent": 1.69,
    "volume": 50000000
  },
  "company_info": {
    "name": "Apple Inc.",
    "sector": "Technology",
    "market_cap": "2500000000000"
  },
  "market_status": {
    "is_open": true
  }
}
```

### GET `/data/history/{ticker}`
Get historical stock data.

**Parameters:**
- `days` (optional): Number of days of history (default: 30)

**Response:**
```json
{
  "ticker": "AAPL",
  "history": [
    {
      "date": "2024-01-15",
      "open": 148.50,
      "high": 151.20,
      "low": 147.80,
      "close": 150.25,
      "volume": 45000000
    }
  ]
}
```

### POST `/ask`
Analyze investment questions with AI using real-time data.

**Request:**
```json
{
  "ticker": "TSLA",
  "question": "Should I invest in Tesla for long-term growth?"
}
```

**Response:**
```json
{
  "ticker": "TSLA",
  "question": "Should I invest in Tesla for long-term growth?",
  "answer": "Based on the analysis...",
  "stock_data": { "price": 250.50, "change": 5.25 },
  "company_info": { "name": "Tesla Inc.", "sector": "Automotive" },
  "historical_data": [...],
  "context_sources": [...],
  "timestamp": "now"
}
```

### POST `/reports/stock`
Generate and download PDF investment report.

**Request:** Same as `/ask`
**Response:** PDF file download

### GET `/history`
Get recent query history.

**Parameters:**
- `limit` (optional): Number of queries to return (default: 10)

### GET `/history/{ticker}`
Get query history for specific ticker.

## Project Structure

```
├── services/
│   ├── __init__.py          # Services package
│   └── finage_fetcher.py    # Finage API integration
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # SQLite database manager
│   ├── vector_store.py      # FAISS vector operations
│   ├── ai_pipeline.py       # LangChain AI pipeline
│   └── pdf_generator.py     # PDF report generation
├── frontend/
│   ├── index.html           # Main UI
│   ├── style.css            # Styling
│   └── script.js            # Frontend logic
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## Usage

1. **Start the backend server** (see setup instructions above)
2. **Open the frontend** in your browser
3. **Enter a stock ticker** (e.g., TSLA, AAPL, MSFT) - live data will auto-load
4. **View real-time stock data** and 30-day price chart
5. **Ask your investment question**
6. **Click "Get AI Analysis"** for AI insights with real-time data
7. **Click "Generate PDF Report"** for a comprehensive downloadable report

## Sample Questions

- "Should I invest in Tesla for long-term growth?"
- "What are the risks of investing in Apple stock?"
- "How does Microsoft compare to other tech stocks?"
- "Is NVIDIA a good buy in the current market?"

## Technical Details

### Real-time Data Integration
The application integrates with Finage API to provide:
- Live stock quotes with price changes
- Company fundamentals (sector, market cap, P/E ratio)
- Historical OHLC data for charting
- Market status information

### Vector Store
The application uses FAISS for semantic search over financial documents. The vector store is pre-populated with sample financial analyses and market insights.

### AI Pipeline
Uses LangChain to orchestrate:
1. Real-time data fetching from Finage API
2. Query embedding generation
3. Vector similarity search
4. Context retrieval and enhancement with live data
5. OpenAI GPT response generation

### Database Schema
```sql
CREATE TABLE queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    stock_data TEXT,
    company_info TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Security Notes

- **API Key Protection**: Never commit your `.env` file
- **CORS**: Configured for development (update for production)
- **Input Validation**: Basic validation implemented
- **Rate Limiting**: Consider adding for production use

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Ensure `.env` file exists with valid `OPENAI_API_KEY`

2. **"Finage API key not found"**
   - Ensure `.env` file exists with valid `FINAGE_API_KEY`
   - Check your Finage account for API limits

3. **"Module not found" errors**
   - Run `pip install -r requirements.txt`

4. **CORS errors in browser**
   - Ensure backend is running on `127.0.0.1:8000`
   - Check browser console for specific CORS issues

5. **FAISS installation issues**
   - Try `pip install faiss-cpu` instead of `faiss-gpu`

6. **Chart not displaying**
   - Ensure Chart.js is loaded from CDN
   - Check browser console for JavaScript errors

### Performance Tips

- Real-time data is cached briefly to avoid API rate limits
- Vector store is cached after first load
- SQLite database grows with usage
- PDF reports are stored in `reports/` directory
- Consider cleanup scripts for production

### API Rate Limits

- **Finage Free Tier**: 100 requests/day
- **OpenAI**: Depends on your plan
- Consider implementing caching for production use

## License

This project is for educational and demonstration purposes.

## Disclaimer

This application provides educational information only and is not personalized financial advice. Always consult with qualified financial professionals before making investment decisions.