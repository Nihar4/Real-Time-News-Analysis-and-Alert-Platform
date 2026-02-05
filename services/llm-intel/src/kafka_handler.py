import asyncio
import json
import structlog
from typing import AsyncIterator, Optional
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = structlog.get_logger()

class KafkaHandler:
    """Handle Kafka producer and consumer operations"""
    
    def __init__(
        self,
        bootstrap_servers: str,
        consumer_group: str,
        input_topic: str,
        output_topic: Optional[str] = None
    ):
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self.input_topic = input_topic
        self.output_topic = output_topic
        
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        
    async def start(self):
        """Initialize Kafka consumer and producer"""
        # Create consumer
        self.consumer = AIOKafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.consumer_group,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        await self.consumer.start()
        logger.info("kafka_consumer_started", topic=self.input_topic)
        
        # Create producer if output topic specified
        if self.output_topic:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info("kafka_producer_started", topic=self.output_topic)
    
    async def stop(self):
        """Stop Kafka consumer and producer"""
        if self.consumer:
            await self.consumer.stop()
            logger.info("kafka_consumer_stopped")
        
        if self.producer:
            await self.producer.stop()
            logger.info("kafka_producer_stopped")
    
    async def consume_messages(self) -> AsyncIterator[dict]:
        """Consume messages from Kafka topic"""
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")
        
        try:
            async for message in self.consumer:
                yield message.value
        except KafkaError as e:
            logger.error("kafka_consume_error", error=str(e))
            raise
    
    async def publish_message(self, message: dict):
        """Publish message to output topic"""
        if not self.producer:
            raise RuntimeError("Producer not started or no output topic specified.")
        
        try:
            await self.producer.send(self.output_topic, value=message)
            logger.debug("message_published", topic=self.output_topic)
        except KafkaError as e:
            logger.error("kafka_publish_error", error=str(e))
            raise

