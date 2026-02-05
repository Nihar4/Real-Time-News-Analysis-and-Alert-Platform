#!/usr/bin/env python3
"""
Service 1: News Fetcher
Fetches news from RSS feeds and publishes to Kafka topic: news.raw.fetched
"""
import asyncio
import yaml
import hashlib
import psycopg2
from typing import List
from datetime import datetime
from .settings import settings
from .utils.app_logger import get_logger
from .utils.state_store import RedisDedupeStore
from .fetchers.rss_fetcher import RSSFetcher
from .producers.kafka_producer import KafkaJSONProducer

log = get_logger("main")

def load_feeds(path: str) -> List[str]:
    """Load RSS feed URLs from YAML file."""
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    feeds = data.get("feeds", [])
    return [u.strip() for u in feeds if u and isinstance(u, str)]

async def run_once(producer: KafkaJSONProducer, fetcher: RSSFetcher, feeds: List[str], dedupe: RedisDedupeStore):
    """Run one cycle of RSS fetching and publishing."""
    cnt_in, cnt_out = 0, 0
    
    async for feed_title, entry in fetcher.stream_entries(feeds, dedupe):
        cnt_in += 1
        
        # Create article ID from URL
        article_id = hashlib.md5(entry["link"].encode()).hexdigest()
        
        # Check if already seen
        if dedupe.seen(article_id):
            continue
        
        # Create minimal output per spec: title, source, URL, publish_time
        output = {
            "article_id": article_id,
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "source": feed_title,
            "publish_time": entry.get("published", ""),
            "fetched_at": datetime.now().isoformat()
        }
        
        # Insert into DB
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
                    INSERT INTO articles (id, source_url, source_name, title, published_at, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_url) DO NOTHING
                """, (
                    article_id,
                    output["url"],
                    output["source"],
                    output["title"],
                    output["publish_time"] if output["publish_time"] else None,
                    output["fetched_at"]
                ))
                conn.commit()
            conn.close()
        except Exception as e:
            log.error(f"Failed to insert article {article_id} into DB: {e}")
            # Continue to publish to Kafka? Or skip? 
            # If DB fails, we probably shouldn't publish to avoid data inconsistency.
            # But for now, let's log and continue, or maybe skip.
            # Let's skip publishing if DB write fails to ensure consistency.
            continue
        
        # Send to Kafka
        await producer.send(key=article_id, value=output)
        cnt_out += 1
    
    log.info(f"Completed processing {len(feeds)} feeds. Entries processed: {cnt_in}, produced: {cnt_out}")

async def wait_for_kafka(settings, max_retries: int = 30, retry_delay: float = 2.0):
    """Wait for Kafka to be available."""
    log.info("Waiting for Kafka to be available...")
    
    for attempt in range(max_retries):
        try:
            producer = KafkaJSONProducer(settings)
            await producer.start()
            await producer.stop()
            log.info("Kafka is available!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                log.info(f"Kafka not ready yet (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay)
            else:
                log.error(f"Failed to connect to Kafka after {max_retries} attempts: {e}")
                return False
    
    return False

async def main():
    """Main function to run the RSS fetcher service."""
    # Wait for Kafka to be available
    if not await wait_for_kafka(settings):
        log.error("Failed to connect to Kafka. Exiting.")
        return
    
    # Load feeds
    feeds = load_feeds(settings.feeds_file)
    if not feeds:
        log.warning("No feeds configured. Add some to feeds.yaml.")
        return
    
    log.info(f"Loaded {len(feeds)} RSS feeds")
    
    # Initialize components
    dedupe = RedisDedupeStore(settings.redis_host, settings.redis_port, settings.redis_db)
    fetcher = RSSFetcher(timeout=settings.http_timeout, rate_limit_delay=settings.rate_limit_delay)
    producer = KafkaJSONProducer(settings)
    
    # Start producer
    await producer.start()
    
    try:
        log.info(f"Starting RSS fetcher service. Polling every {settings.poll_interval_seconds} seconds")
        
        while True:
            try:
                await run_once(producer, fetcher, feeds, dedupe)
            except Exception as e:
                log.exception(f"Cycle failed: {e}")
            
            log.info(f"Waiting {settings.poll_interval_seconds} seconds before next cycle...")
            await asyncio.sleep(settings.poll_interval_seconds)
            
    finally:
        await producer.stop()

if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except Exception:
        pass
    asyncio.run(main())
