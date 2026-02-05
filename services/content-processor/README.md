# Content Processor Service

Downloads and extracts clean text content from article URLs.

## Overview

The Content Processor service consumes raw article metadata from Kafka, downloads the full article content, extracts clean text, and publishes the processed content for LLM analysis.

## Features

- **Full Text Extraction**: Downloads and parses article HTML
- **HTML Cleaning**: Removes ads, navigation, and boilerplate using Trafilatura
- **Language Detection**: Identifies article language
- **Auto-Translation**: Optionally translates non-English articles

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka broker address |
| `KAFKA_TOPIC_RAW_ARTICLES` | `news.raw.fetched` | Input topic |
| `KAFKA_TOPIC_PROCESSED_ARTICLES` | `news.cleaned` | Output topic |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout |
| `USER_AGENT` | `Mozilla/5.0...` | User agent for requests |
| `AUTO_TRANSLATE_NON_ENGLISH` | `true` | Enable translation |

## Running Locally

⚠️ **This service runs locally for development** (not in Docker for easier debugging):

```bash
cd services/content-processor

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export KAFKA_BOOTSTRAP_SERVERS=localhost:19092
export DB_HOST=localhost

# Run
python -m src.main
```

## Output

Publishes to `news.cleaned` topic with extracted article text.
