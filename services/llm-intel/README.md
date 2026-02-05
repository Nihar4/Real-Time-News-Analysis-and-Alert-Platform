# LLM Intelligence Service

AI-powered analysis service that extracts structured business events from article text.

## Overview

The LLM Intelligence service uses Large Language Models (Llama 3.1, Gemini) to analyze article content and extract structured business events including company names, event types, and confidence scores.

## Features

- **Multi-Provider LLM**: Supports Cerebras (Llama) and Google Gemini
- **API Key Rotation**: Automatically rotates through multiple API keys
- **Automatic Failover**: Falls back to alternative providers on errors
- **Structured Extraction**: Outputs JSON with company, event type, summary
- **Confidence Scoring**: Rates extraction confidence (0-1)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka broker |
| `KAFKA_TOPIC_INPUT` | `news.cleaned` | Input topic |
| `KAFKA_TOPIC_OUTPUT` | `news.enriched` | Output topic |
| `CEREBRAS_API_KEYS` | - | Comma-separated Cerebras keys |
| `GEMINI_API_KEYS` | - | Comma-separated Gemini keys |
| `CEREBRAS_MAX_TOKENS` | `4096` | Max response tokens |
| `CEREBRAS_TEMPERATURE` | `0.7` | LLM temperature |

## Running Locally

```bash
cd services/llm-intel
pip install -r requirements.txt
python -m src.main
```

## Docker

```bash
docker compose up llm-intel
```

## Output Schema

```json
{
  "primary_company": "Apple Inc.",
  "event_type": "Product Launch",
  "event_summary": "Apple announced new iPhone...",
  "confidence_score": 0.95,
  "event_date": "2024-12-07"
}
```
