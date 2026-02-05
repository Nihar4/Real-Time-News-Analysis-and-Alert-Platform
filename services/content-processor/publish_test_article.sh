#!/bin/bash

# Publish a fake Amazon product launch article to news.cleaned topic for testing LLM service

# Generate a random UUID for the article ID
ARTICLE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

ARTICLE_JSON='{
  "article_id": "'"$ARTICLE_ID"'",
  "url": "https://example.com/amazon-cloud-ai-launch",
  "title": "Amazon Launches Revolutionary AI-Powered Cloud Service",
  "content": "Amazon Web Services today announced the launch of AWS IntelliCloud, a groundbreaking artificial intelligence platform designed to revolutionize cloud computing. The new service combines advanced machine learning capabilities with scalable infrastructure to help businesses automate complex workflows and gain deeper insights from their data. AWS IntelliCloud features natural language processing, computer vision, and predictive analytics tools that can be seamlessly integrated into existing applications. The platform is expected to compete directly with similar offerings from Google Cloud and Microsoft Azure. Amazon CEO Andy Jassy stated that IntelliCloud represents the companys commitment to democratizing AI technology and making it accessible to organizations of all sizes. The service will be available in multiple AWS regions starting next month, with pricing based on usage and computational resources consumed.",
  "source": "TechNews Daily",
  "publish_time": "2025-12-03T08:00:00Z",
  "fetched_at": "2025-12-03T08:40:00",
  "processed_at": "2025-12-03T08:41:00",
  "word_count": 142,
  "extraction_method": "trafilatura"
}'

echo "Publishing test Amazon article..."
echo "Article ID: $ARTICLE_ID"

# First, insert the article into the database
echo "Inserting article into database..."
/usr/local/bin/docker exec pg-newsinsight psql -U app -d newsinsight -c "
INSERT INTO articles (id, source_url, source_name, title, clean_text, published_at, fetched_at)
VALUES (
  '$ARTICLE_ID',
  'https://example.com/amazon-cloud-ai-launch',
  'TechNews Daily',
  'Amazon Launches Revolutionary AI-Powered Cloud Service',
  'Amazon Web Services today announced the launch of AWS IntelliCloud, a groundbreaking artificial intelligence platform designed to revolutionize cloud computing. The new service combines advanced machine learning capabilities with scalable infrastructure to help businesses automate complex workflows and gain deeper insights from their data. AWS IntelliCloud features natural language processing, computer vision, and predictive analytics tools that can be seamlessly integrated into existing applications. The platform is expected to compete directly with similar offerings from Google Cloud and Microsoft Azure. Amazon CEO Andy Jassy stated that IntelliCloud represents the companys commitment to democratizing AI technology and making it accessible to organizations of all sizes. The service will be available in multiple AWS regions starting next month, with pricing based on usage and computational resources consumed.',
  '2025-12-03T08:00:00Z',
  '2025-12-03T08:40:00Z'
);"

# Then publish to Kafka
echo "Publishing to Kafka topic news.cleaned..."
echo "$ARTICLE_JSON" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)))" | /usr/local/bin/docker exec -i newsinsight-redpanda-1 \
  rpk topic produce news.cleaned \
  --key "$ARTICLE_ID"

echo "✅ Test article published! Watch the LLM intel logs."
