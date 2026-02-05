# Event Mapper Service

Persists deduplicated events to the database.

## Overview

The Event Mapper service is the final stage of the data pipeline. It consumes unique, enriched articles and persists them as structured events in PostgreSQL.

## Features

- **Database Persistence**: Stores events in PostgreSQL
- **Company Matching**: Links events to tracked companies
- **Event Classification**: Categorizes events by type
- **Notification Triggers**: Publishes events for notification service

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka broker |
| `KAFKA_TOPIC_INPUT` | `news.deduped` | Input topic |
| `KAFKA_TOPIC_OUTPUT` | `events.created` | Output topic |
| `DB_HOST` | `postgres` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `newsinsight` | Database name |
| `DB_USER` | `app` | Database user |
| `DB_PASSWORD` | `app` | Database password |

## Running Locally

```bash
cd services/event-mapper
pip install -r requirements.txt
python -m src.main
```

## Docker

```bash
docker compose up event-mapper
```

## Database Schema

Events are stored in the `events` table:
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    title VARCHAR(500),
    description TEXT,
    event_type VARCHAR(100),
    confidence_score FLOAT,
    source_url VARCHAR(1000),
    event_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```
