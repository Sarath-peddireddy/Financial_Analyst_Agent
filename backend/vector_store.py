import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
from typing import List, Dict, Any

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.documents = []
        self.metadata = []
        self.index_path = "faiss_index.bin"
        self.docs_path = "documents.pkl"
        
        # Load existing index if available
        self.load_index()
        
        # If no index exists, create with sample financial documents
        if self.index.ntotal == 0:
            self.populate_sample_data()
    
    def populate_sample_data(self):
        """Populate the vector store with sample financial documents."""
        sample_docs = [
            {
                "content": "Tesla (TSLA) is a leading electric vehicle manufacturer with strong growth potential in the EV market. The company has shown consistent revenue growth and expanding global presence.",
                "metadata": {"ticker": "TSLA", "type": "analysis", "date": "2024"}
            },
            {
                "content": "Apple (AAPL) maintains strong fundamentals with robust cash flow, innovative product pipeline, and dominant market position in consumer electronics.",
                "metadata": {"ticker": "AAPL", "type": "analysis", "date": "2024"}
            },
            {
                "content": "Microsoft (MSFT) benefits from cloud computing growth through Azure, strong enterprise software sales, and AI integration across products.",
                "metadata": {"ticker": "MSFT", "type": "analysis", "date": "2024"}
            },
            {
                "content": "NVIDIA (NVDA) is positioned well for AI boom with dominant GPU market share, data center growth, and strong partnerships in AI infrastructure.",
                "metadata": {"ticker": "NVDA", "type": "analysis", "date": "2024"}
            },
            {
                "content": "Amazon (AMZN) shows diversified revenue streams through e-commerce, AWS cloud services, and advertising business with strong competitive moats.",
                "metadata": {"ticker": "AMZN", "type": "analysis", "date": "2024"}
            },
            {
                "content": "Market volatility in 2024 has been driven by inflation concerns, interest rate changes, and geopolitical tensions affecting global supply chains.",
                "metadata": {"ticker": "MARKET", "type": "market_analysis", "date": "2024"}
            },
            {
                "content": "Electric vehicle adoption is accelerating globally with government incentives, improving battery technology, and expanding charging infrastructure.",
                "metadata": {"ticker": "EV_SECTOR", "type": "sector_analysis", "date": "2024"}
            },
            {
                "content": "Technology sector outlook remains positive despite short-term headwinds, with AI, cloud computing, and digital transformation driving long-term growth.",
                "metadata": {"ticker": "TECH_SECTOR", "type": "sector_analysis", "date": "2024"}
            }
        ]
        
        for doc in sample_docs:
            self.add_document(doc["content"], doc["metadata"])
        
        self.save_index()
    
    def add_document(self, content: str, metadata: Dict[str, Any]):
        """Add a document to the vector store."""
        # Generate embedding
        embedding = self.model.encode([content])
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embedding)
        
        # Add to index
        self.index.add(embedding)
        
        # Store document and metadata
        self.documents.append(content)
        self.metadata.append(metadata)
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx != -1:  # Valid result
                results.append({
                    "content": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "score": float(score)
                })
        
        return results
    
    def save_index(self):
        """Save the FAISS index and documents to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.docs_path, 'wb') as f:
            pickle.dump({"documents": self.documents, "metadata": self.metadata}, f)
    
    def load_index(self):
        """Load the FAISS index and documents from disk."""
        if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.docs_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data["documents"]
                self.metadata = data["metadata"]