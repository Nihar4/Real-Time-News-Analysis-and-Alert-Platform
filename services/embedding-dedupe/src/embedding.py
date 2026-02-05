import torch
from sentence_transformers import SentenceTransformer
from huggingface_hub import login
import structlog
from typing import List
from src.config import settings

logger = structlog.get_logger()

class EmbeddingModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("initializing_embedding_model", 
                   model=settings.embedding_model_id, 
                   device=self.device)
        
        # Login to Hugging Face
        if settings.huggingface_token:
            login(token=settings.huggingface_token)
            
        try:
            self.model = SentenceTransformer(settings.embedding_model_id).to(self.device)
            logger.info("embedding_model_loaded", 
                       params=sum(p.numel() for p in self.model.parameters()))
        except Exception as e:
            logger.error("embedding_model_load_failed", error=str(e))
            raise

    def generate(self, text: str) -> List[float]:
        """Generate embedding for a single text string"""
        try:
            # Generate embedding
            # normalize_embeddings=True is usually good for cosine similarity
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            return []
