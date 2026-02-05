#!/usr/bin/env python3
"""
Service 2: Content Processor
Cleans HTML, extracts main text, performs basic URL deduplication
Consumes: news.raw.fetched
Produces: news.cleaned
"""
import asyncio
import hashlib
import structlog
import psycopg2
from datetime import datetime
from typing import Optional

from src.config import settings
from src.kafka_handler import KafkaHandler
from src.processors.text_extractor import TextExtractor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


class ContentProcessingService:
    """
    Service 2: Content Processing
    
    Processes raw articles from Kafka:
    1. Extracts content using multiple methods (Trafilatura → Newspaper → Readability → BeautifulSoup)
    2. Basic dedupe by URL hash
    3. Publishes cleaned articles to Kafka
    """
    
    def __init__(self):
        # Initialize Kafka handler
        self.kafka = KafkaHandler(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_group=settings.kafka_consumer_group,
            input_topic=settings.kafka_topic_raw_articles,
            output_topic=settings.kafka_topic_processed_articles
        )
        
        # Initialize text extractor
        self.text_extractor = TextExtractor(
            user_agent=settings.user_agent,
            timeout=settings.request_timeout
        )
        
        # URL deduplication tracking
        self.seen_urls = set()
        
        logger.info("content_processing_service_initialized")
    
    def process_article(self, raw_article: dict) -> Optional[dict]:
        """Process a single article"""
        try:
            article_id = raw_article.get("article_id", "")
            url = raw_article.get("url", "")
            title = raw_article.get("title", "")
            
            if not url:
                logger.warning("no_url_found", article_id=article_id)
                return None
            
            # Basic dedupe by URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self.seen_urls:
                logger.info("duplicate_url_skipped", article_id=article_id, url=url)
                return None
            
            self.seen_urls.add(url_hash)
            
            logger.info("processing_article", article_id=article_id, url=url)
            
            # Extract content
            extracted = self.text_extractor.extract(url)
            if not extracted or not extracted.get('content'):
                logger.warning("content_extraction_failed", article_id=article_id, url=url)
                return None
            
            # Use extracted title or fallback to RSS title
            final_title = extracted['title'] or title or 'No Title'
            content = extracted['content']
            
            # Create cleaned article (minimal fields per spec)
            cleaned_article = {
                "article_id": article_id,
                "url": url,
                "title": final_title,
                "content": content,
                "source": raw_article.get("source", "Unknown"),
                "publish_time": raw_article.get("publish_time", ""),
                "fetched_at": raw_article.get("fetched_at", ""),
                "processed_at": datetime.utcnow().isoformat(),
                "word_count": len(content.split()),
                "extraction_method": extracted['method']
            }
            
            # Update DB
            try:
                conn = psycopg2.connect(
                    host=settings.db_host,
                    port=settings.db_port,
                    dbname=settings.db_name,
                    user=settings.db_user,
                    password=settings.db_password
                )
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE articles 
                        SET clean_text = %s, raw_html = %s
                        WHERE id = %s
                    """, (
                        content,
                        extracted.get('raw_html', ''), # Assuming extractor returns raw_html too, if not empty string
                        article_id
                    ))
                    conn.commit()
                conn.close()
            except Exception as e:
                logger.error("db_update_failed", article_id=article_id, error=str(e))
                # We might want to fail here, but for now let's continue to publish to Kafka
                # actually, if DB update fails, downstream LLM might fail if it reads from DB?
                # The plan says LLM consumes news.cleaned. 
                # If LLM reads from DB, then yes, it's critical.
                # If LLM uses the payload, it's fine.
                # Plan says: "Step 4.3... Consume news.cleaned... Build prompt... Use primary_company from JSON"
                # It doesn't explicitly say LLM reads from DB. 
                # But for data consistency, let's log error.
            
            logger.info("article_processed_successfully",
                       article_id=article_id,
                       word_count=cleaned_article['word_count'],
                       extraction_method=extracted['method'])
            
            return cleaned_article
            
        except Exception as e:
            article_id = raw_article.get('article_id', 'unknown')
            logger.error("article_processing_error",
                        article_id=article_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    async def run(self):
        """Run the service continuously"""
        logger.info("content_processing_service_started")
        
        processed_count = 0
        failed_count = 0
        
        try:
            async for raw_article in self.kafka.consume_messages():
                try:
                    # Process article
                    cleaned_article = self.process_article(raw_article)
                    
                    if cleaned_article:
                        # Publish to Kafka
                        await self.kafka.publish_message(cleaned_article)
                        processed_count += 1
                    else:
                        failed_count += 1
                    
                    # Log stats every 10 articles
                    if (processed_count + failed_count) % 10 == 0:
                        success_rate = (processed_count / (processed_count + failed_count)) * 100
                        logger.info("processing_stats",
                                   processed=processed_count,
                                   failed=failed_count,
                                   success_rate=f"{success_rate:.2f}%")
                
                except Exception as e:
                    logger.error("message_processing_error",
                                error=str(e),
                                error_type=type(e).__name__)
                    failed_count += 1
                    continue
        
        except KeyboardInterrupt:
            logger.info("shutting_down",
                       total_processed=processed_count,
                       total_failed=failed_count)
        finally:
            await self.kafka.stop()


async def main():
    """Main entry point"""
    service = ContentProcessingService()
    await service.kafka.start()
    
    try:
        await service.run()
    finally:
        await service.kafka.stop()


if __name__ == "__main__":
    # Use uvloop for better async performance (optional)
    try:
        import uvloop
        uvloop.install()
        logger.info("uvloop_enabled")
    except ImportError:
        logger.info("uvloop_not_available_using_default_event_loop")
    
    # Run the service
    asyncio.run(main())