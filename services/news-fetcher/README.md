# News Fetcher Service

Polls RSS feeds and news APIs to discover new articles for processing.

## Overview

The News Fetcher service is the first stage of the FutureFeed data pipeline. It continuously monitors configured news sources and publishes discovered article metadata to Kafka.

## Features

- **RSS Feed Polling**: Configurable polling interval for RSS feeds
- **Deduplication**: Tracks already-fetched URLs to avoid duplicates
- **Rate Limiting**: Respects source rate limits to prevent blocking
- **HTTP State Management**: Persistent state across restarts

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka broker address |
| `KAFKA_TOPIC` | `news.raw.fetched` | Output topic for raw articles |
| `POLL_INTERVAL_SECONDS` | `30` | How often to poll feeds |
| `HTTP_TIMEOUT` | `15` | HTTP request timeout |
| `RATE_LIMIT_DELAY` | `1.0` | Delay between requests |

## Running Locally

```bash
cd services/news-fetcher
pip install -r requirements.txt
python -m src.main
```

## Docker

```bash
docker compose up news-fetcher
```

## Output

Publishes to `news.raw.fetched` topic with schema:
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "source": "Reuters",
  "published_at": "2024-12-07T12:00:00Z"
}
```
