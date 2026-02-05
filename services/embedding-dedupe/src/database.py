import psycopg2
from psycopg2.extras import Json
from pgvector.psycopg2 import register_vector
import structlog
from typing import List, Optional, Tuple
from src.config import settings

logger = structlog.get_logger()

class VectorStore:
    def __init__(self):
        self.conn = None
        self.connect()
        
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=settings.db_host,
                port=settings.db_port,
                dbname=settings.db_name,
                user=settings.db_user,
                password=settings.db_password
            )
            # Register pgvector extension
            register_vector(self.conn)
            logger.info("connected_to_postgres")
        except Exception as e:
            logger.error("postgres_connection_failed", error=str(e))
            raise

    def find_similar_event(self, embedding: List[float], threshold: float = 0.85) -> Optional[Tuple[str, float]]:
        """
        Find the most similar event in the database.
        Returns (event_id, similarity_score) if found, else None.
        """
        if not self.conn or self.conn.closed:
            self.connect()
            
        try:
            with self.conn.cursor() as cur:
                # Cosine similarity is 1 - cosine_distance
                # We want similarity > threshold
                query = """
                SELECT id, 1 - (embedding <=> %s::vector) as similarity
                FROM events
                WHERE 1 - (embedding <=> %s::vector) > %s
                ORDER BY similarity DESC
                LIMIT 1;
                """
                cur.execute(query, (embedding, embedding, threshold))
                result = cur.fetchone()
                
                if result:
                    return str(result[0]), float(result[1])
                return None
                
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            self.conn.rollback()
            return None

    def get_max_similarity(self, embedding: List[float]) -> Optional[float]:
        """
        Get the maximum similarity score for an embedding against all existing events.
        Returns the highest similarity score, or 0.0 if no events exist.
        """
        if not self.conn or self.conn.closed:
            self.connect()
            
        try:
            with self.conn.cursor() as cur:
                # Get the highest similarity score
                query = """
                SELECT MAX(1 - (embedding <=> %s::vector)) as max_similarity
                FROM events
                WHERE embedding IS NOT NULL;
                """
                cur.execute(query, (embedding,))
                result = cur.fetchone()
                
                if result and result[0] is not None:
                    return float(result[0])
                return 0.0
                
        except Exception as e:
            logger.error("max_similarity_search_failed", error=str(e))
            self.conn.rollback()
            return 0.0

    def update_event_embedding(self, event_id: str, embedding: List[float]) -> bool:
        """
        Update the embedding for an existing event.
        """
        if not self.conn or self.conn.closed:
            self.connect()
            
        try:
            with self.conn.cursor() as cur:
                query = """
                UPDATE events
                SET embedding = %s::vector
                WHERE id = %s
                """
                cur.execute(query, (embedding, event_id))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error("embedding_update_failed", error=str(e), event_id=event_id)
            self.conn.rollback()
            return False

    def close(self):
        if self.conn:
            self.conn.close()
