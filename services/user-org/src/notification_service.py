import asyncio
import json
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from src.config import settings
from src.kafka_handler import KafkaHandler
from src.database import AsyncSessionLocal
from src.models import Event, User, Membership, Organization, Company
from src.email_service import email_service

logger = structlog.get_logger()

class NotificationService:
    """
    Handles event notifications:
    1. Consumes events.created topic
    2. Fetches event details and subscribed members
    3. Sends email alerts
    """
    
    def __init__(self):
        self.kafka = KafkaHandler(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_group="user-org-notification-group",
            input_topic="events.created"
        )
        logger.info("notification_service_initialized")
        
    async def process_event_notification(self, msg: dict):
        """Process a single event notification message"""
        event_id = msg.get("event_id")
        org_ids = msg.get("organization_ids", [])
        
        if not event_id or not org_ids:
            logger.warning("invalid_notification_message", msg=msg)
            return

        logger.info("processing_event_notification", event_id=event_id, org_count=len(org_ids))
        
        async with AsyncSessionLocal() as db:
            # 1. Fetch Event Details
            result = await db.execute(
                select(Event)
                .options(selectinload(Event.primary_company))
                .where(Event.id == event_id)
            )
            event = result.scalars().first()
            
            if not event:
                logger.error("event_not_found", event_id=event_id)
                return
            
            # Prepare email data
            event_title = event.headline_summary or "New Event Detected"
            event_desc = event.short_summary or event.detailed_summary or "No description available."
            company_name = event.primary_company.display_name if event.primary_company else "Unknown Company"
            event_date = event.created_at.strftime("%Y-%m-%d")
            
            # 2. For each organization, fetch members and send emails
            for org_id in org_ids:
                # Fetch members
                result = await db.execute(
                    select(User)
                    .join(Membership)
                    .where(Membership.organization_id == org_id)
                )
                members = result.scalars().all()
                
                logger.info("sending_alerts_for_org", org_id=org_id, member_count=len(members))
                
                for member in members:
                    try:
                        email_service.send_event_alert_email(
                            to_email=member.email,
                            to_name=member.name,
                            event_title=event_title,
                            event_description=event_desc,
                            company_name=company_name,
                            event_date=event_date,
                            event_id=str(event.id)
                        )
                    except Exception as e:
                        logger.error("failed_to_send_alert_email", 
                                    user_email=member.email, 
                                    error=str(e))

    async def run(self):
        """Run the notification service loop"""
        await self.kafka.start()
        logger.info("notification_service_started")
        
        try:
            async for msg in self.kafka.consume_messages():
                try:
                    await self.process_event_notification(msg)
                except Exception as e:
                    logger.error("notification_processing_error", error=str(e))
        except Exception as e:
             logger.error("notification_service_fatal_error", error=str(e))
        finally:
            await self.kafka.stop()

# Singleton instance
notification_service = NotificationService()
