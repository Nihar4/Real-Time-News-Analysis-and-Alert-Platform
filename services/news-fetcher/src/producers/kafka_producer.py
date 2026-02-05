import asyncio
import json
from typing import Any, Optional
from aiokafka import AIOKafkaProducer
from ..utils.app_logger import get_logger
from ..settings import settings

log = get_logger("kafka_producer")

class KafkaJSONProducer:
    def __init__(self, settings):
        self.settings = settings
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        """Start the Kafka producer."""
        log.info(f"Starting Kafka producer for topic: {self.settings.kafka_topic}")
        
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            client_id=self.settings.client_id,
            acks=self.settings.kafka_acks,
            compression_type=self.settings.kafka_compression_type,
            enable_idempotence=True,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        await self._producer.start()
        log.info("Kafka producer started successfully")

    async def stop(self):
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            log.info("Kafka producer stopped")

    async def send(self, key: str, value: Any):
        """Send a message to Kafka."""
        if not self._producer:
            raise RuntimeError("Producer not started")
        
        try:
            await self._producer.send(
                topic=self.settings.kafka_topic,
                key=key,
                value=value
            )
            log.debug(f"Sent message with key: {key}")
        except Exception as e:
            log.error(f"Failed to send message: {e}")
            raise
