#!/usr/bin/env python3
"""
Service 4: Embedding & Dedupe
Consumes enriched news, generates vector embeddings, checks for duplicates in DB,
and publishes unique events to 'news.deduped'.
"""
import asyncio
import json
import structlog
from kafka import KafkaConsumer, KafkaProducer
from src.config import settings
from src.embedding import EmbeddingModel
from src.database import VectorStore

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

class EmbeddingDedupeService:
    def __init__(self):
        # Initialize Kafka Consumer
        self.consumer = KafkaConsumer(
            settings.kafka_topic_input,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest'
        )
        
        # Initialize Kafka Producer
        self.producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # Initialize Model and DB
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        
        logger.info("embedding_dedupe_service_initialized")

    def run(self):
        """Run the service loop"""
        logger.info("embedding_dedupe_service_started")
        
        try:
            for message in self.consumer:
                article = message.value
                article_id = article.get("article_id")
                title = article.get("title", "")
                summary = article.get("detailed_summary") or article.get("short_summary") or ""
                
                # Combine title and summary for rich embedding
                text_to_embed = f"{title}\n\n{summary}"
                
                logger.info("processing_article", article_id=article_id, title=title[:50])
                
                # 1. Generate Embedding
                embedding = self.embedding_model.generate(text_to_embed)
                if not embedding:
                    logger.warning("skipping_article_no_embedding", article_id=article_id)
                    continue
                
                # 2. Check for Duplicates in DB
                similar_event = self.vector_store.find_similar_event(
                    embedding, 
                    threshold=settings.similarity_threshold
                )
                
                if similar_event:
                    existing_id, score = similar_event
                    logger.info("duplicate_detected", 
                               article_id=article_id, 
                               existing_event_id=existing_id, 
                               similarity_score=score)
                    
                    # Mark as duplicate in payload with similarity score
                    article["is_duplicate"] = True
                    article["duplicate_of"] = existing_id
                    article["max_similarity_score"] = round(score, 4)
                    article["similarity_threshold"] = settings.similarity_threshold
                    
                    self.producer.send(settings.kafka_topic_output, value=article)
                    continue
                
                # 3. Update Event with Embedding
                # We expect 'event_id' in the message from LLM service
                event_id = article.get("event_id")
                if event_id:
                    success = self.vector_store.update_event_embedding(event_id, embedding)
                    if success:
                        logger.info("event_embedding_updated", event_id=event_id)
                        
                        # Get max similarity score for this article (for monitoring purposes)
                        max_sim = self.vector_store.get_max_similarity(embedding)
                        
                        # 4. Publish Unique Event with similarity info
                        article["embedding_id"] = "vector_stored_in_db"
                        article["is_duplicate"] = False
                        article["max_similarity_score"] = round(max_sim, 4) if max_sim else 0.0
                        article["similarity_threshold"] = settings.similarity_threshold
                        self.producer.send(settings.kafka_topic_output, value=article)
                        logger.info("unique_event_published", article_id=article_id, max_similarity=max_sim)
                    else:
                        logger.error("failed_to_update_embedding", event_id=event_id)
                else:
                    logger.warning("missing_event_id_in_message", article_id=article_id)
                    # Fallback: If no event_id (legacy message?), just publish without DB update?
                    # No, strict mode.
                    pass
                
        except Exception as e:
            logger.error("service_loop_failed", error=str(e))
            raise
        finally:
            self.consumer.close()
            self.producer.close()
            self.vector_store.close()

if __name__ == "__main__":
    service = EmbeddingDedupeService()
    service.run()
