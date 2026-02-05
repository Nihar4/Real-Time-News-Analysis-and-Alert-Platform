#!/usr/bin/env python3
"""
Service 5.2: Event Mapper
Maps unique events to subscribed organizations
Consumes: news.deduped
Produces: events.created
"""
import asyncio
import structlog
import psycopg2
import json
from datetime import datetime
from typing import Optional, List

from src.config import settings
from src.kafka_handler import KafkaHandler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


class EventMapperService:
    """
    Service 5.2: Event Mapper
    
    Processes deduped events:
    1. Checks if event is unique (is_duplicate == False)
    2. Finds relevant organizations subscribed to the company
    3. Creates organization_events rows
    4. Publishes events.created
    """
    
    def __init__(self):
        # Initialize Kafka handler
        self.kafka = KafkaHandler(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_group=settings.kafka_consumer_group,
            input_topic=settings.kafka_topic_input,
            output_topic=settings.kafka_topic_output
        )
        
        logger.info("event_mapper_service_initialized")
    
    def get_db_connection(self):
        return psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password
        )

    def process_event(self, event_msg: dict) -> Optional[dict]:
        """Process a single event message"""
        try:
            # 1. Check if duplicate
            if event_msg.get("is_duplicate", False):
                logger.info("skipping_duplicate_event", event_id=event_msg.get("event_id"))
                return None
            
            event_id = event_msg.get("event_id")
            slug = event_msg.get("primary_company_slug")
            
            if not event_id or not slug:
                logger.warning("missing_event_id_or_slug", event_id=event_id, slug=slug)
                return None
            
            logger.info("processing_unique_event", event_id=event_id, slug=slug)
            
            conn = self.get_db_connection()
            org_ids = []
            
            with conn.cursor() as cur:
                # 2. Find Company ID
                cur.execute("SELECT id FROM companies WHERE slug = %s", (slug,))
                res = cur.fetchone()
                if not res:
                    logger.warning("company_not_found_for_slug", slug=slug)
                    return None
                company_id = res[0]
                
                # 3. Find Subscribed Organizations
                cur.execute("""
                    SELECT organization_id 
                    FROM organization_companies 
                    WHERE company_id = %s
                """, (company_id,))
                rows = cur.fetchall()
                
                # 4. Insert organization_events
                for row in rows:
                    org_id = row[0]
                    cur.execute("""
                        INSERT INTO organization_events (organization_id, event_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (org_id, event_id))
                    org_ids.append(str(org_id))
                
                conn.commit()
            conn.close()
            
            if not org_ids:
                logger.info("no_subscriptions_found", slug=slug, event_id=event_id)
                return None
            
            # 5. Create Output Message
            output_msg = {
                "event_id": event_id,
                "organization_ids": org_ids,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("event_mapped_to_orgs", 
                       event_id=event_id, 
                       org_count=len(org_ids))
            
            return output_msg
            
        except Exception as e:
            logger.error("event_processing_error",
                        event_id=event_msg.get('event_id'),
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    async def run(self):
        """Run the service continuously"""
        logger.info("event_mapper_service_started")
        
        processed_count = 0
        
        try:
            async for msg in self.kafka.consume_messages():
                try:
                    # Process event
                    output_msg = self.process_event(msg)
                    
                    if output_msg:
                        # Publish to Kafka
                        await self.kafka.publish_message(output_msg)
                        processed_count += 1
                    
                except Exception as e:
                    logger.error("message_processing_error",
                                error=str(e),
                                error_type=type(e).__name__)
                    continue
        
        except KeyboardInterrupt:
            logger.info("shutting_down", total_processed=processed_count)
        finally:
            await self.kafka.stop()


async def main():
    """Main entry point"""
    service = EventMapperService()
    await service.kafka.start()
    
    try:
        await service.run()
    finally:
        await service.kafka.stop()


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
        logger.info("uvloop_enabled")
    except ImportError:
        logger.info("uvloop_not_available_using_default_event_loop")
    
    asyncio.run(main())
