import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "financial_queries.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    stock_data TEXT,
                    company_info TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def save_query(self, ticker: str, question: str, answer: str, stock_data: str = None, company_info: str = None) -> int:
        """Save a query and its answer to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO queries (ticker, question, answer, stock_data, company_info, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ticker, question, answer, stock_data, company_info, datetime.now()))
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent queries from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ticker, question, answer, stock_data, company_info, timestamp
                FROM queries
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_queries_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Get all queries for a specific ticker."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ticker, question, answer, stock_data, company_info, timestamp
                FROM queries
                WHERE ticker = ?
                ORDER BY timestamp DESC
            """, (ticker,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]