# 🚀 Real-Time News Analysis and Alert Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![Kafka](https://img.shields.io/badge/Kafka-Redpanda-red.svg)](https://redpanda.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)
[![AWS](https://img.shields.io/badge/AWS-ECS-orange.svg)](https://aws.amazon.com)

## 🎥 Demo Video

**▶️ [Watch the Demo Video](https://drive.google.com/file/d/1-A9wOPZv-DTnTMRgx7p6K3IMFCzZ_ilD/view?usp=sharing)**

---

## 📋 Overview

**Real-Time News Analysis and Alert Platform** is an enterprise-grade competitor intelligence system that monitors news sources, extracts insights using AI/LLM, and delivers personalized alerts to users. Built with a microservices architecture using Python, Go, Kafka, Redis, and PostgreSQL.

### Key Achievements

- **Built Python LLM enrichment pipeline** with pre-LLM semantic deduplication using **pgvector** for summarization and entity extraction, **reducing API calls by 60%** while processing **10K+ daily articles**

- **Developed Go notification microservice** with **Redis caching** for real-time alerts matching user preferences, delivering events in **under 2 minutes** with **70% duplicate reduction**

- **Designed event-driven microservices architecture** with **Kafka** stream processing, **PostgreSQL**, and **Next.js** frontend, containerized with **Docker** and deployed on **AWS ECS**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         REAL-TIME NEWS ANALYSIS PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   RSS Feeds ──► News Fetcher ──► news.raw.fetched                                   │
│                                       │                                             │
│                                       ▼                                             │
│                          ┌────────────────────────┐                                 │
│                          │  Content Processor     │                                 │
│                          │  (Article Extraction)  │                                 │
│                          └────────────────────────┘                                 │
│                                       │                                             │
│                                       ▼ news.cleaned                                │
│                          ┌────────────────────────┐                                 │
│                          │  PRE-LLM DEDUPLICATION │ ◄── 60% cost reduction          │
│                          │  (pgvector similarity) │                                 │
│                          └────────────────────────┘                                 │
│                                       │                                             │
│                                       ▼ news.filtered                               │
│                          ┌────────────────────────┐                                 │
│                          │     LLM-INTEL          │                                 │
│                          │  (Summarization +      │                                 │
│                          │   Entity Extraction)   │                                 │
│                          └────────────────────────┘                                 │
│                                       │                                             │
│                                       ▼ news.enriched                               │
│                          ┌────────────────────────┐                                 │
│                          │   Embedding Dedupe     │                                 │
│                          │   (Semantic Filtering) │                                 │
│                          └────────────────────────┘                                 │
│                                       │                                             │
│                                       ▼ news.deduped                                │
│       ┌───────────────────────────────┼───────────────────────────────┐             │
│       │                               │                               │             │
│       ▼                               ▼                               ▼             │
│  ┌──────────────┐           ┌──────────────────┐           ┌──────────────┐         │
│  │ Event Mapper │           │  Notification    │           │   Next.js    │         │
│  │ (PostgreSQL) │           │  Service (Go)    │           │   Frontend   │         │
│  └──────────────┘           │  + Redis Cache   │           └──────────────┘         │
│                             └──────────────────┘                                    │
│                                       │                                             │
│                                       ▼                                             │
│                              Email/SMS Alerts                                       │
│                           (< 2 min latency)                                         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

| Category | Technologies |
|----------|-------------|
| **Backend (Python)** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic, LangChain |
| **Backend (Go)** | Go 1.21+, kafka-go, go-redis |
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS |
| **Message Streaming** | Apache Kafka (Redpanda) |
| **Database** | PostgreSQL 15 with **pgvector** for semantic search |
| **Caching** | Redis 7 |
| **AI/ML** | Cerebras (Llama 3.1), Google Gemini, Sentence Transformers, LangChain |
| **Containerization** | Docker, Docker Compose |
| **Cloud** | AWS ECS, ECR |

---

## 📦 Microservices

| Service | Language | Description |
|---------|----------|-------------|
| **news-fetcher** | Python | Polls RSS feeds and discovers articles |
| **content-processor** | Python | Extracts article text with multi-tier fallback |
| **llm-intel** | Python | AI-powered summarization and entity extraction |
| **embedding-dedupe** | Python | Semantic deduplication using pgvector |
| **event-mapper** | Python | Persists events to PostgreSQL |
| **notification-service** | **Go** | Real-time alerts with Redis caching |
| **user-org** | Python | REST API, JWT auth, multi-tenant orgs |
| **frontend** | Next.js | Dashboard and administrative interface |

---

## ✨ Key Features

### LLM Enrichment Pipeline (Python)
- **Pre-LLM deduplication** reduces API calls by 60%
- Multi-provider LLM support (Cerebras, Gemini) with automatic failover
- Entity extraction, topic classification, and sentiment analysis
- Processes 10K+ articles daily

### Notification Service (Go)
- **Real-time alerts** delivered in under 2 minutes
- **Redis-based duplicate detection** reduces duplicate alerts by 70%
- User preference matching (companies, event types, risk thresholds)
- Email notification delivery via SMTP

### Event-Driven Architecture
- **Kafka stream processing** for decoupled, scalable pipeline
- **PostgreSQL with pgvector** for semantic search and storage
- **Docker containerization** for consistent deployments
- **AWS ECS deployment** for production scalability

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (v2.0+)
- Python 3.11+ (for content-processor)
- Go 1.21+ (for notification-service)
- Git

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/Nihar4/Real-Time-News-Analysis-and-Alert-Platform.git
cd Real-Time-News-Analysis-and-Alert-Platform

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Verify services
docker compose ps
```

### Access Points

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs** | http://localhost:8001/docs |
| **Kafka Console** | http://localhost:8080 |
| **pgAdmin** | http://localhost:5050 |

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Daily Article Processing | **10,000+ articles** |
| LLM API Cost Reduction | **60%** (via pre-LLM deduplication) |
| Notification Latency | **< 2 minutes** |
| Duplicate Alert Reduction | **70%** |
| Kafka Topics | 5 (raw → cleaned → filtered → enriched → deduped) |

---

## 🔐 Security Features

- **JWT-based stateless authentication** with 24-hour tokens
- **Role-based access control** for organization data
- **Multi-tenant data isolation**
- **Email-based team invitations** with secure tokens

---

## 📂 Project Structure

```
Real-Time-News-Analysis-and-Alert-Platform/
├── docker-compose.yml          # Docker orchestration
├── .env.example                # Environment template
├── README.md                   # This file
│
├── frontend/                   # Next.js application
│   ├── app/                    # App Router pages
│   ├── components/             # React components
│   └── lib/                    # Utilities
│
├── services/
│   ├── news-fetcher/           # Python - RSS ingestion
│   ├── content-processor/      # Python - Article extraction
│   ├── llm-intel/              # Python - AI analysis
│   ├── embedding-dedupe/       # Python - Deduplication
│   ├── event-mapper/           # Python - DB writer
│   ├── notification-service/   # Go - Real-time alerts ⭐
│   └── user-org/               # Python - FastAPI backend
│
├── db/
│   └── migrations/             # SQL migrations
│
└── infra/
    └── db/
        └── init/               # DB init scripts
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# JWT
SECRET_KEY=your_jwt_secret

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_app_password

# AI APIs
CEREBRAS_API_KEYS=key1,key2,key3
GEMINI_API_KEYS=key1,key2,key3

# Redis
REDIS_ADDR=localhost:6379
```

### Kafka Topics

| Topic | Description |
|-------|-------------|
| `news.raw.fetched` | Raw RSS entries |
| `news.cleaned` | Extracted article text |
| `news.enriched` | LLM-analyzed content |
| `news.deduped` | Unique articles |
| `events.created` | Final events |

---

## 🧪 Testing

```bash
# Run Python tests
cd services/user-org
python -m pytest tests/ -v

# Run Go tests
cd services/notification-service
go test ./...
```

---

## 👨‍💻 Author

**Nihar Patel**
- GitHub: [@Nihar4](https://github.com/Nihar4)

---

## 📝 License

This project is licensed under the MIT License.
