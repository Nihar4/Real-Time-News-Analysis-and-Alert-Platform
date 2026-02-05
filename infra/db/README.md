# NewsInsight Database Setup

## Overview

PostgreSQL database with **pgvector** extension for topic management and article enrichment.

## Database Tables

### User Management Tables (Existing)

- ✅ `users` - User accounts
- ✅ `user_queries` - User search queries and preferences
- ✅ `alert_history` - History of alerts sent to users

### Topic Management Tables (New)

- ✅ `topics` - Canonical topics with searchable terms and embeddings
- ✅ `article_topics` - Article-to-topic mappings with relevance scores
- ✅ `topic_searchable_terms_log` - Audit log of new searchable terms
- ✅ `llm_validation_log` - LLM validation decisions for borderline matches

## Environment Variables

Create a `.env` file in this directory:

```env
# PostgreSQL Configuration
POSTGRES_DB=newsinsight_db
POSTGRES_USER=newsinsight_user
POSTGRES_PASSWORD=your_secure_password_here
```

## Docker Compose Commands

```bash
# Start PostgreSQL + pgAdmin
docker compose up -d

# View logs
docker compose logs -f postgres

# Stop services
docker compose down

# Reset database (⚠️ DANGER: Deletes all data)
docker compose down -v

# Access PostgreSQL CLI
docker exec -it pg-newsinsight psql -U newsinsight_user -d newsinsight_db
```

## Access pgAdmin

1. Open browser: http://localhost:5050
2. Login:
   - Email: `admin@newsinsight.com`
   - Password: `admin123`
3. Add server:
   - Host: `postgres`
   - Port: `5432`
   - Database: `newsinsight_db`
   - Username: `newsinsight_user`
   - Password: (from your .env file)

## Schema Features

### pgvector Integration

The database uses **pgvector** extension for embedding similarity search:

```sql
-- Vector similarity search (cosine similarity)
SELECT
    id,
    canonical_name,
    display_name,
    1 - (canonical_embedding <=> query_embedding) as similarity
FROM topics
WHERE 1 - (canonical_embedding <=> query_embedding) > 0.80
ORDER BY canonical_embedding <=> query_embedding
LIMIT 10;
```

### Helper Functions

#### 1. Search Topics by Term

```sql
-- Find all topics matching a search term
SELECT * FROM search_topics_by_term('artificial intelligence');
```

#### 2. Auto-Update Topic Stats

Topics automatically update their `article_count` and `last_seen` when new articles are linked via a trigger.

## Sample Queries

### Find all topics in a category

```sql
SELECT
    id,
    canonical_name,
    display_name,
    article_count,
    array_length(searchable_terms, 1) as term_count
FROM topics
WHERE category = 'Technology'
ORDER BY article_count DESC;
```

### Get articles for a topic

```sql
SELECT
    at.article_id,
    at.relevance_score,
    at.matched_search_terms,
    at.match_method
FROM article_topics at
WHERE at.topic_id = 123
ORDER BY at.relevance_score DESC;
```

### Find most popular topics

```sql
SELECT
    id,
    display_name,
    article_count,
    subscriber_count,
    last_seen
FROM topics
WHERE is_active = TRUE
ORDER BY article_count DESC
LIMIT 20;
```

### LLM validation statistics

```sql
SELECT
    llm_decision,
    final_action,
    COUNT(*) as count,
    AVG(processing_time_ms) as avg_time_ms
FROM llm_validation_log
GROUP BY llm_decision, final_action
ORDER BY count DESC;
```

### Recent searchable terms added

```sql
SELECT
    tst.search_term,
    t.display_name as topic_name,
    tst.frequency_count,
    tst.added_by_method,
    tst.added_at
FROM topic_searchable_terms_log tst
JOIN topics t ON t.id = tst.topic_id
ORDER BY tst.added_at DESC
LIMIT 50;
```

## Database Maintenance

### Rebuild vector index (if needed)

```sql
-- Drop old index
DROP INDEX IF EXISTS idx_topics_embedding;

-- Recreate with adjusted list count based on topic count
-- Rule of thumb: lists = sqrt(total_rows)
CREATE INDEX idx_topics_embedding ON topics
    USING ivfflat (canonical_embedding vector_cosine_ops)
    WITH (lists = 100);  -- Adjust based on number of topics
```

### Vacuum and analyze

```sql
-- Reclaim space and update statistics
VACUUM ANALYZE topics;
VACUUM ANALYZE article_topics;
```

## Troubleshooting

### pgvector extension not found

```bash
# Ensure you're using ankane/pgvector image
docker compose down
docker compose pull
docker compose up -d
```

### Database connection refused

```bash
# Check if PostgreSQL is healthy
docker compose ps

# Check logs
docker compose logs postgres

# Ensure network exists
docker network create newsinsight-net
docker compose up -d
```

### Schema not initialized

```bash
# Check init scripts were run
docker compose logs postgres | grep "NewsInsight Database Schema"

# If not found, remove volume and recreate
docker compose down -v
docker compose up -d
```

## Integration with Services

### Service 3: Topic Management

The Topic Management service will:

1. Read from Kafka topic: `processed-articles`
2. Extract topics from `search_terms` using embeddings
3. Match against existing topics in `topics` table
4. Create new topics or update existing ones
5. Store mappings in `article_topics`
6. Publish enriched data to Kafka topic: `enriched-articles`

### Connection String

```python
# Python (SQLAlchemy)
DATABASE_URL = "postgresql://newsinsight_user:password@postgres:5432/newsinsight_db"

# Or from environment
DB_HOST=postgres
DB_PORT=5432
DB_NAME=newsinsight_db
DB_USER=newsinsight_user
DB_PASSWORD=your_password
```

## Next Steps

1. ✅ Database schema created
2. ⏳ Create Topic Management service (Service 3)
3. ⏳ Implement embedding generation
4. ⏳ Implement topic matching logic
5. ⏳ Deploy and test

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Arrays](https://www.postgresql.org/docs/current/arrays.html)
- [IVFFlat Index](https://github.com/pgvector/pgvector#ivfflat)
