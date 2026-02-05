import asyncio
import json
from aiokafka import AIOKafkaProducer
from .config import settings
from .app_logger import get_logger

log = get_logger("kafka_producer")

class KafkaProducerSingleton:
    _producer: AIOKafkaProducer | None = None
    _lock = asyncio.Lock()
    
    def __init__(self, settings):
        self.settings = settings

    async def start(self):
        raw_acks = str(self.settings.kafka_acks).strip().lower()
        if raw_acks in {"all", "-1"}:
            acks_value = -1
        elif raw_acks in {"0", "1"}:
            acks_value = int(raw_acks)
        else:
            log.warning("Invalid ACKS value '%s'; defaulting to -1 (all)", raw_acks)
            acks_value = -1

        # Idempotent producer requires acks=-1; enforce if needed
        enable_idempotence = True
        if enable_idempotence and acks_value != -1:
            log.warning("Idempotence enabled but ACKS=%s; forcing ACKS to -1 (all)", acks_value)
            acks_value = -1

        # Determine compression type with a safe fallback if lz4 is not available
        compression = self.settings.kafka_compression_type
        if isinstance(compression, str) and compression.lower() == "lz4":
            try:
                import lz4.frame  # noqa: F401
            except Exception:
                log.warning("lz4 library not available; falling back to gzip compression")
                compression = "gzip"

        async with self._lock:
            if self._producer is None:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    client_id=self.settings.client_id,
                    acks=acks_value,
                    enable_idempotence=enable_idempotence,
                    compression_type=compression,
                    linger_ms=50,
                    max_batch_size=32768,
                    request_timeout_ms=20000,
                    retry_backoff_ms=200,
                    key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                await self._producer.start()
                log.info("Kafka producer started")

    async def stop(self):
        async with self._lock:
            if self._producer is not None:
                await self._producer.stop()
                self._producer = None

    async def send(self, topic: str, key: str | None, value: dict):
        if self._producer is None:
            raise RuntimeError("Kafka producer not started")
        await self._producer.send_and_wait(topic, key=key, value=value)

producer = KafkaProducerSingleton(settings)
