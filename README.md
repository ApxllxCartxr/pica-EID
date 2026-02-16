# PRISMID — Personnel Identity & Role Governance System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Commercial-grade Personnel Identity and Role Governance System with opaque ID generation, three-tier RBAC, intern lifecycle automation, and bi-directional spreadsheet integration.

---

## Features

| Feature | Description |
|---------|-------------|
| **Opaque User IDs** | SHA-256 + Base62 + Luhn checksum — non-decryptable, 21-character IDs |
| **Three-Tier RBAC** | Viewer → Admin → Superadmin access hierarchy |
| **Intern Lifecycle** | Automated expiry, 7-day warnings, and one-click conversion to employee |
| **Role Governance** | Clearance levels, soft-delete, assignment protection |
| **Spreadsheet Sync** | Bi-directional Google Sheets API + Excel (.xlsx) import/export |
| **Audit Trail** | Full audit log with previous/new value tracking |
| **Premium Dashboard** | Dark glass-morphism SPA with real-time stats and search |
| **Production Ready** | Docker Compose, NGINX reverse proxy, Celery workers, rate limiting |

## Architecture

```
┌──────────────────────────────────────────────────┐
│  NGINX (Reverse Proxy + Rate Limiting)           │
├──────────────────────────────────────────────────┤
│  FastAPI Application                             │
│  ├── Auth API (JWT + bcrypt)                     │
│  ├── Users API (CRUD + Search + Conversion)      │
│  ├── Roles API (CRUD + Soft-Delete)              │
│  ├── Audit API (Filtered Logs)                   │
│  ├── Sheets API (Excel + Google Sheets)          │
│  └── Dashboard SPA (HTML/CSS/JS)                 │
├──────────────────────────────────────────────────┤
│  Celery Workers              │  Redis Cache      │
│  ├── Intern Expiry (daily)   │  ├── Warnings     │
│  └── Sheet Sync (15 min)     │  └── Sessions     │
├──────────────────────────────────────────────────┤
│  PostgreSQL 15 (Primary Database)                │
└──────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/prismid.git
cd prismid
cp .env.example .env
# Edit .env with your secrets
```

### 2. Run with Docker
```bash
docker-compose up -d
```

### 3. Seed Database
```bash
docker-compose exec app python scripts/seed.py
```

### 4. Access Dashboard
Open **http://localhost** and login with the seeded superadmin credentials.

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Testing
```bash
pytest tests/ -v --tb=short
```

## Project Structure
```
PRISMID/
├── app/
│   ├── api/            # FastAPI route handlers
│   ├── core/           # ID generator, security, permissions
│   ├── models/         # SQLAlchemy ORM models (9 tables)
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Excel & Google Sheets services
│   ├── static/         # Dashboard SPA (HTML/CSS/JS)
│   ├── tasks/          # Celery background tasks
│   ├── config.py       # Environment configuration
│   ├── database.py     # Database engine & sessions
│   └── main.py         # FastAPI application entry
├── alembic/            # Database migrations
├── nginx/              # NGINX reverse proxy config
├── scripts/            # Seed & backup scripts
├── tests/              # Pytest test suite
├── docker-compose.yml  # Full stack orchestration
├── Dockerfile          # Application container
└── requirements.txt    # Python dependencies
```

## Security

- **Authentication**: JWT with refresh tokens, bcrypt password hashing
- **Authorization**: Three-tier RBAC enforced at middleware level
- **Rate Limiting**: NGINX-level throttling (API: 30/s, Search: 10/s)
- **Input Validation**: Pydantic schemas for all requests
- **Audit Trail**: Every mutation logged with actor and timestamp
- **ID Opacity**: User IDs are non-reversible — no category information leaks

## License

MIT © 2026
