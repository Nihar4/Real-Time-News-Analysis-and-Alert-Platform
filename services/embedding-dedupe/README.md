# Embedding Dedupe Service

Semantic deduplication service using vector embeddings.

## Overview

The Embedding Dedupe service uses transformer-based embeddings to detect semantically similar articles and prevent duplicate events from being stored.

## Features

- **Vector Embeddings**: Converts articles to 384-dimensional vectors
- **Cosine Similarity**: Compares articles against recent entries
- **Configurable Threshold**: Default 0.85 similarity for duplicates
- **HuggingFace Integration**: Uses sentence-transformers models

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka broker |
| `KAFKA_TOPIC_INPUT` | `news.enriched` | Input topic |
| `KAFKA_TOPIC_OUTPUT` | `news.deduped` | Output topic |
| `HUGGINGFACE_TOKEN` | - | HuggingFace API token |
| `EMBEDDING_MODEL_ID` | `google/embeddinggemma-300M` | Model to use |
| `SIMILARITY_THRESHOLD` | `0.85` | Duplicate threshold |
| `DB_HOST` | `postgres` | Database host |
| `DB_PASSWORD` | `app` | Database password |

## Running Locally

```bash
cd services/embedding-dedupe
pip install -r requirements.txt
python -m src.main
```

## Docker

```bash
docker compose up embedding-dedupe
```

## How It Works

1. Receive enriched article from Kafka
2. Generate embedding vector using transformer model
3. Query database for recent similar articles
4. If similarity > threshold, mark as duplicate
5. If unique, publish to output topic
