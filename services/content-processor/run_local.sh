#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the service directory
cd "$SCRIPT_DIR"

# Environment variables for local execution
export KAFKA_BOOTSTRAP_SERVERS=localhost:19092
export KAFKA_TOPIC_RAW_ARTICLES=news.raw.fetched
export KAFKA_TOPIC_PROCESSED_ARTICLES=news.cleaned
export KAFKA_CONSUMER_GROUP=content-processing-group-local
export REQUEST_TIMEOUT=30
export USER_AGENT="Mozilla/5.0 (compatible; NewsBot/1.0)"
export AUTO_TRANSLATE_NON_ENGLISH=true
export LOG_LEVEL=INFO

# Database config (exposed on localhost:5432)
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=newsinsight
export DB_USER=app
export DB_PASSWORD=app

# Add current directory to python path
export PYTHONPATH=$PYTHONPATH:.

echo "Starting Content Processor locally..."
echo "Working directory: $(pwd)"
echo "Kafka: $KAFKA_BOOTSTRAP_SERVERS"
echo "DB: $DB_HOST:$DB_PORT"

# Run the service
python -m src.main
