# 🚀 Database Deployment Guide

## Prerequisites

✅ Docker and Docker Compose installed  
✅ Port 5432 available (or change in docker-compose.yml)  
✅ Port 5050 available for pgAdmin

## Step 1: Create Environment File

Create `.env` file in `/Users/spartan/Downloads/Nihar/Coding/newsinsight/infra/db/`:

```bash
cd /Users/spartan/Downloads/Nihar/Coding/newsinsight/infra/db

cat > .env << 'EOF'
POSTGRES_DB=newsinsight_db
POSTGRES_USER=newsinsight_user
POSTGRES_PASSWORD=newsinsight_password_2024
EOF
```

## Step 2: Create Docker Network

```bash
# Create network if it doesn't exist
docker network create newsinsight-net 2>/dev/null || echo "Network already exists"
```

## Step 3: Deploy Database

```bash
cd /Users/spartan/Downloads/Nihar/Coding/newsinsight/infra/db

# Start PostgreSQL with pgvector + pgAdmin
docker compose up -d

# Wait for database to be ready
docker compose logs -f postgres | grep -m 1 "database system is ready"
```

## Step 4: Verify Installation

```bash
# Check container status
docker compose ps

# Should show:
# NAME                  IMAGE                      STATUS
# pg-newsinsight        ankane/pgvector:latest     Up (healthy)
# pgadmin-newsinsight   dpage/pgadmin4:8.11        Up

# Check schema was created
docker compose logs postgres | grep "NewsInsight Database Schema"

# Should output:
# ✅ NewsInsight Database Schema Created Successfully!
# - 3 User Management Tables (users, user_queries, alert_history)
# - 4 Topic Management Tables (topics, article_topics, topic_searchable_terms_log, llm_validation_log)
```

## Step 5: Test Database Connection

```bash
# Connect to PostgreSQL CLI
docker exec -it pg-newsinsight psql -U newsinsight_user -d newsinsight_db

# Run test queries
\dt  -- List all tables
\d topics  -- Describe topics table
\d article_topics  -- Describe article_topics table

# Check pgvector extension
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

# Should show: vector | 0.7.x

# Test vector similarity (example)
SELECT 1 - (ARRAY[1,2,3]::vector <=> ARRAY[1,2,4]::vector) as similarity;

# Exit psql
\q
```

## Step 6: Access pgAdmin (Optional)

1. Open browser: **http://localhost:5050**
2. Login:
   - Email: `admin@newsinsight.com`
   - Password: `admin123`
3. Add New Server:
   - **General Tab:**
     - Name: `NewsInsight DB`
   - **Connection Tab:**
     - Host: `postgres`
     - Port: `5432`
     - Maintenance database: `newsinsight_db`
     - Username: `newsinsight_user`
     - Password: `newsinsight_password_2024` (from your .env)
   - Click **Save**

## Step 7: View Tables in pgAdmin

Navigate to:

```
Servers > NewsInsight DB > Databases > newsinsight_db > Schemas > public > Tables
```

You should see:

- ✅ users
- ✅ user_queries
- ✅ alert_history
- ✅ topics (NEW)
- ✅ article_topics (NEW)
- ✅ topic_searchable_terms_log (NEW)
- ✅ llm_validation_log (NEW)

## Step 8: Insert Test Data (Optional)

```bash
docker exec -it pg-newsinsight psql -U newsinsight_user -d newsinsight_db << 'EOF'

-- Insert a test topic
INSERT INTO topics (
    canonical_name,
    display_name,
    searchable_terms,
    canonical_embedding,
    category
) VALUES (
    'artificial_intelligence',
    'Artificial Intelligence',
    ARRAY['AI', 'artificial intelligence', 'machine learning', 'ML', 'deep learning', 'neural networks', 'AI technology'],
    array_fill(0.1, ARRAY[384])::vector,
    'Technology'
);

-- Insert another test topic
INSERT INTO topics (
    canonical_name,
    display_name,
    searchable_terms,
    canonical_embedding,
    category
) VALUES (
    'climate_change',
    'Climate Change',
    ARRAY['climate change', 'global warming', 'climate crisis', 'climate emergency', 'carbon emissions', 'greenhouse gases'],
    array_fill(0.2, ARRAY[384])::vector,
    'Environment'
);

-- Verify insertion
SELECT id, canonical_name, display_name, array_length(searchable_terms, 1) as term_count, category FROM topics;

EOF
```

## Database Schema Summary

### User Management (Existing)

| Table           | Purpose                        |
| --------------- | ------------------------------ |
| `users`         | User accounts                  |
| `user_queries`  | Search queries and preferences |
| `alert_history` | Alert delivery history         |

### Topic Management (New)

| Table                        | Purpose                                               |
| ---------------------------- | ----------------------------------------------------- |
| `topics`                     | Canonical topics with embeddings and searchable terms |
| `article_topics`             | Links articles to topics with relevance scores        |
| `topic_searchable_terms_log` | Audit log of new searchable terms                     |
| `llm_validation_log`         | LLM decisions for borderline matches                  |

## Connection Info for Services

Add to your service `.env` files:

```env
# Database Connection
DB_HOST=postgres
DB_PORT=5432
DB_NAME=newsinsight_db
DB_USER=newsinsight_user
DB_PASSWORD=newsinsight_password_2024

# Or as connection string
DATABASE_URL=postgresql://newsinsight_user:newsinsight_password_2024@postgres:5432/newsinsight_db
```

## Troubleshooting

### Issue: Network not found

```bash
docker network create newsinsight-net
docker compose up -d
```

### Issue: Port 5432 already in use

```bash
# Edit docker-compose.yml, change:
ports:
  - "55432:5432"  # Use different external port

# Then restart
docker compose down
docker compose up -d
```

### Issue: Schema not created

```bash
# Remove volume and recreate
docker compose down -v
docker compose up -d

# Check logs
docker compose logs postgres | tail -50
```

### Issue: pgvector not working

```bash
# Ensure using correct image
docker compose down
docker compose pull
docker compose up -d

# Verify extension
docker exec -it pg-newsinsight psql -U newsinsight_user -d newsinsight_db -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

## Maintenance Commands

```bash
# View logs
docker compose logs -f postgres

# Restart database
docker compose restart postgres

# Stop database
docker compose stop

# Remove everything (⚠️ DATA LOSS)
docker compose down -v

# Backup database
docker exec pg-newsinsight pg_dump -U newsinsight_user newsinsight_db > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20241018.sql | docker exec -i pg-newsinsight psql -U newsinsight_user -d newsinsight_db
```

## Next Steps

1. ✅ Database deployed successfully
2. ⏳ Update topic-extractor service to output enriched articles with topic metadata
3. ⏳ Create Topic Management service (Service 3) to:
   - Consume from `enriched-articles` Kafka topic
   - Extract and match topics using embeddings
   - Store in PostgreSQL `topics` and `article_topics` tables
   - Publish final enriched data back to Kafka

## Quick Reference

| Resource                 | URL/Command                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| PostgreSQL CLI           | `docker exec -it pg-newsinsight psql -U newsinsight_user -d newsinsight_db` |
| pgAdmin                  | http://localhost:5050                                                       |
| Database Host (internal) | `postgres:5432`                                                             |
| Database Host (external) | `localhost:5432`                                                            |
| Container Name           | `pg-newsinsight`                                                            |
| Network                  | `newsinsight-net`                                                           |

---

**🎉 Database is now ready for Topic Management service!**
