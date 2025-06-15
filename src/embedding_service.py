import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize embedding service with a pre-trained model"""
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Loaded embedding model: {model_name} (dim: {self.embedding_dim})")
    
    def create_article_embedding(self, title: str, description: str, category: str = None) -> np.ndarray:
        """Create embedding vector for an article"""
        # Combine title, description, and category for richer representation
        text_parts = [title, description]
        if category:
            text_parts.append(f"Category: {category}")
        
        combined_text = " ".join(filter(None, text_parts))
        
        # Generate embedding
        embedding = self.model.encode(combined_text, normalize_embeddings=True)
        return embedding
    
    def create_preference_embedding(self, keywords: List[str], categories: List[str] = None) -> np.ndarray:
        """Create embedding vector for user preferences"""
        text_parts = keywords.copy()
        if categories:
            text_parts.extend([f"Category: {cat}" for cat in categories])
        
        combined_text = " ".join(text_parts)
        embedding = self.model.encode(combined_text, normalize_embeddings=True)
        return embedding
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        return cosine_similarity([embedding1], [embedding2])[0][0]
    
    def find_similar_articles(self, preference_embedding: np.ndarray, 
                            article_embeddings: List[np.ndarray], 
                            threshold: float = 0.5) -> List[Tuple[int, float]]:
        """Find articles similar to user preferences"""
        similarities = []
        for i, article_embedding in enumerate(article_embeddings):
            similarity = self.calculate_similarity(preference_embedding, article_embedding)
            if similarity >= threshold:
                similarities.append((i, similarity))
        
        # Sort by similarity (highest first)
        return sorted(similarities, key=lambda x: x[1], reverse=True)
    
    def serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Serialize embedding for database storage"""
        return pickle.dumps(embedding)
    
    def deserialize_embedding(self, embedding_bytes: bytes) -> np.ndarray:
        """Deserialize embedding from database"""
        return pickle.loads(embedding_bytes)