# User-Org Service

Backend API service for authentication, organizations, and user management.

## Overview

The User-Org service is the core backend API built with FastAPI. It handles user authentication, organization management, company tracking, event retrieval, task management, and email notifications.

## Features

- **JWT Authentication**: Stateless token-based authentication (24h expiry)
- **Password Security**: bcrypt hashing with work factor 12
- **Role-Based Access Control**: Owner, Admin, Member roles
- **Organization Management**: Multi-tenant organization support
- **Company Tracking**: Track competitors per organization
- **Task Management**: Create and assign tasks from events
- **Email Notifications**: Gmail SMTP integration for alerts

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register user and create org |
| POST | `/auth/login` | Login and receive JWT |
| GET | `/me` | Get current user profile |

### Organizations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/org/{id}` | Get organization details |
| GET | `/org/{id}/members` | List members |
| POST | `/org/{id}/invite` | Invite member via email |

### Companies & Events
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/org/{id}/companies` | List tracked companies |
| POST | `/org/{id}/companies` | Add company to track |
| GET | `/org/{id}/events` | List detected events |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/org/{id}/tasks` | List tasks |
| POST | `/org/{id}/tasks` | Create task |
| PUT | `/tasks/{id}` | Update task |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `postgres` | Database host |
| `DB_PASSWORD` | `app` | Database password |
| `SECRET_KEY` | - | JWT signing secret |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PASSWORD` | - | Gmail app password |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend URL for emails |

## Running Locally

```bash
cd services/user-org
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

## Docker

```bash
docker compose up user-org
```

## API Documentation

Interactive API docs available at: http://localhost:8001/docs

## Testing

```bash
cd services/user-org
pip install pytest pytest-asyncio httpx
python -m pytest tests/ -v
```
