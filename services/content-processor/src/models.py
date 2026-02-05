from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List, Union
import hashlib

class RawArticle(BaseModel):
    """Input from Kafka"""
    id: str
    url: Optional[str] = None
    link: Optional[str] = None  # Alternative field name
    title: Optional[str] = None
    summary: Optional[str] = None
    authors: Optional[List[Union[str, dict]]] = None
    published: Optional[str] = None
    feed_title: Optional[str] = None
    fetched_at: Optional[str] = None
    
    @field_validator('authors', mode='before')
    @classmethod
    def normalize_authors(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            normalized = []
            for author in v:
                if isinstance(author, dict) and 'name' in author:
                    normalized.append(author['name'])
                elif isinstance(author, str):
                    normalized.append(author)
            return normalized
        return v

class ProcessedArticle(BaseModel):
    """Output to Kafka"""
    # Core fields
    article_id: str
    url: str
    title: str
    content: str  # Original content
    clean_text: str  # Cleaned text (same as content for now)
    
    # Metadata
    author: Optional[str] = None
    publish_date: Optional[str] = None
    source: str
    fetch_timestamp: str
    process_timestamp: str
    
    # Content analysis
    content_hash: str
    word_count: int
    language: str
    
    # Description and keywords
    description: Optional[str] = None
    image_url: Optional[str] = None
    keywords: List[str] = []
    
    # Translation (if not English)
    translated_title: Optional[str] = None
    translated_content: Optional[str] = None
    
    # Extraction info
    extraction_method: str
    
    def __init__(self, **data):
        if 'process_timestamp' not in data:
            data['process_timestamp'] = datetime.utcnow().isoformat()
        if 'content_hash' not in data and 'clean_text' in data:
            data['content_hash'] = hashlib.sha256(
                data['clean_text'].encode()
            ).hexdigest()
        if 'word_count' not in data and 'clean_text' in data:
            data['word_count'] = len(data['clean_text'].split())
        super().__init__(**data)
    
    def to_kafka_message(self) -> dict:
        """Convert to dict for Kafka"""
        return self.model_dump()
    
    def get_text_for_classification(self) -> str:
        """
        Get text to use for Topic Classification (Service 3)
        Uses English version if available, otherwise original
        """
        if self.translated_title and self.translated_content:
            return f"{self.translated_title}\n\n{self.translated_content}"
        return f"{self.title}\n\n{self.content}"
    
    def get_text_for_embedding(self) -> str:
        """
        Get text to use for Embedding Generation (Service 4)
        Uses English version for better embedding quality
        """
        if self.translated_content:
            return self.translated_content
        return self.content
    
    def get_text_for_clustering(self) -> str:
        """
        Get text to use for Clustering (Service 5)
        Uses English version for consistency
        """
        return self.get_text_for_embedding()