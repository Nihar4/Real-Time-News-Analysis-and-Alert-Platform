import json
import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logger = structlog.get_logger()

class KafkaHandler:
    """Handle Kafka consumer and producer with async operations"""
    
    def __init__(self, bootstrap_servers: str, consumer_group: str,
                 input_topic: str, output_topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.consumer = None
        self.producer = None
        
        logger.info("kafka_handler_initialized",
                   bootstrap_servers=bootstrap_servers,
                   input_topic=input_topic,
                   output_topic=output_topic)
    
    async def start(self):
        """Start Kafka consumer and producer"""
        # Initialize consumer
        self.consumer = AIOKafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.bootstrap_servers.split(','),
            group_id=self.consumer_group,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            max_poll_records=10
        )
        
        # Initialize producer
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            compression_type='gzip'
        )
        
        await self.consumer.start()
        await self.producer.start()
        
        logger.info("kafka_connections_started")
    
    async def stop(self):
        """Stop Kafka consumer and producer"""
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        logger.info("kafka_connections_stopped")
    
    async def consume_messages(self):
        """Async generator that yields messages"""
        async for message in self.consumer:
            yield message.value
    
    async def publish_message(self, message: dict):
        """Publish message to output topic"""
        try:
            await self.producer.send(self.output_topic, value=message)
            logger.debug("message_published",
                        article_id=message.get('article_id'))
        except Exception as e:
            logger.error("kafka_publish_error",
                        article_id=message.get('article_id'),
                        error=str(e))