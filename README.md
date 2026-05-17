# Secure Messenger

This repository contains a simple chat application with a FastAPI backend and a React + Vite frontend.

Purpose: provide a concise, factual reference describing project layout, API endpoints, environment variables, local run/build commands, and deployment notes.

---

## Repository layout (files and purpose)

- `server/` — backend implementation (FastAPI)
  - `server/main.py` — FastAPI app setup, router registration, CORS setup (reads `ALLOWED_ORIGINS`).
  - `server/database.py` — SQLAlchemy engine/session (reads `DATABASE_URL`).
  - `server/routers/` — API routers: `auth_router.py`, `message_router.py`, `stream_router.py`, `group_router.py`.
  - `server/core/` — utilities: `auth.py`, `broadcaster.py`, `membership_cache.py`.
  - `server/services/` — business logic for auth, messages, groups.
  - `server/repositories/` — DB access wrappers.
- `migrations/` and `alembic.ini` — Alembic migration scripts and configuration.
- `client-app/` — React + Vite frontend
  - `client-app/src/api.js` — central API client; uses `import.meta.env.VITE_API_URL || '/'`.
  - `client-app/src/pages/Chat.jsx` — chat UI, message list and input, SSE integration.
  - `client-app/src/pages/Login.jsx`, `Register.jsx` — auth pages.
- `requirements.txt` — Python dependencies.
- `pyproject.toml` — optional project metadata.
- `Dockerfile`, `.dockerignore` — container build files.
- `Procfile` — process command for Procfile-based platforms.

---

## API endpoints (concise reference)

Auth
- `POST /register` — register a new user. Example payload: `{ "username": "u", "password": "p", "email": "e" }`.
- `POST /login` — authenticate and receive JWT access token. Example payload: `{ "username": "u", "password": "p" }`.

Messages
- `GET /messages` — list messages for the authenticated user. Requires Authorization header.
- `POST /messages` — send a message. Typical payload includes `content` and either `recipient_id` or `group_id`.

Groups
- `GET /groups` — list groups.
- `GET /groups/my` — list groups for the authenticated user.
- `POST /groups` — create a group.
- `POST /groups/{id}/join` — request to join a group.
- `GET /groups/{id}/messages` — get group history.

Realtime
- `GET /stream` — SSE endpoint. Requires `Authorization: Bearer <token>` header. Response `Content-Type: text/event-stream`.

---

## Environment variables used by the server

- `DATABASE_URL` — SQLAlchemy connection string. Examples:
  - Local sqlite: `sqlite:///./messenger.db`
  - Postgres: `postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`
- `ALLOWED_ORIGINS` — comma-separated origins for CORS (e.g. `http://localhost:5173,https://app.example.com`).
- `PORT` — optional port used by the `Procfile` or container runtime.

---

## Exact commands — local development

Backend (PowerShell commands):

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
# run server with sqlite
$env:DATABASE_URL = 'sqlite:///./messenger.db'
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (PowerShell):

```powershell
cd client-app
npm install
npm run dev
```

Build frontend with production API base URL:

```powershell
cd client-app
VITE_API_URL=https://api.example.com/ npm run build
```

Docker — build and run backend container:

```powershell
docker build -t secure-messenger:latest .
docker run -e DATABASE_URL="sqlite:///./messenger.db" -p 8000:8000 secure-messenger:latest
```

Alembic migrations (run where `alembic` is available and `DATABASE_URL` is set):

```powershell
alembic upgrade head
```

---

## Notes on realtime (SSE) implementation

- The backend publishes message events to an in-process `broadcaster` when messages are created.
- The `/stream` endpoint subscribes to the broadcaster and sends matching events to the connected client as SSE (`text/event-stream`).
- For horizontal scaling, a central broker (Redis Pub/Sub or similar) is required so events published on one instance are received by subscribers connected to other instances.

---

## Minimal troubleshooting

- If the backend cannot connect to the DB: confirm `DATABASE_URL`, network access, and DB credentials.
- If `psycopg2` fails to install on some platforms: either install OS-level libpq headers or use `psycopg2-binary` in `requirements.txt`.
- If SSE appears buffered by a proxy: verify load balancer/reverse proxy streaming config.

---

If specific sections must be expanded into exact request/response examples or the full API JSON schemas, list which endpoints you want expanded and the README will be updated with those exact examples.
# Secure Messenger

This repository contains a simple chat application with a FastAPI backend and a React + Vite frontend.

This README provides a factual reference: main files, API endpoints, environment variables, and exact commands to run and build the project locally.

---

## Repository layout (files and purpose)

- `server/` — backend implementation (FastAPI)
  - `server/main.py` — FastAPI app setup, router registration, CORS setup (reads `ALLOWED_ORIGINS`).
  - `server/database.py` — SQLAlchemy engine/session (reads `DATABASE_URL`).
  - `server/routers/` — API routers: `auth_router.py`, `message_router.py`, `stream_router.py`, `group_router.py`.
  - `server/core/` — utilities: `auth.py`, `broadcaster.py`, `membership_cache.py`.
  - `server/services/` — business logic for auth, messages, groups.
  - `server/repositories/` — DB access wrappers.
- `migrations/` and `alembic.ini` — Alembic migration scripts and configuration.
- `client-app/` — React + Vite frontend
  - `client-app/src/api.js` — central API client; uses `import.meta.env.VITE_API_URL || '/'`.
  - `client-app/src/pages/Chat.jsx` — chat UI, message list and input, SSE integration.
  - `client-app/src/pages/Login.jsx`, `Register.jsx` — auth pages.
- `requirements.txt` — Python dependencies.
- `pyproject.toml` — optional project metadata.
- `Dockerfile`, `.dockerignore` — container build files.
- `Procfile` — process command for Procfile-based platforms.

---

## API endpoints (concise reference)

Auth
- `POST /register` — register a new user. Example payload: `{ "username": "u", "password": "p", "email": "e" }`.
- `POST /login` — authenticate and receive JWT access token. Example payload: `{ "username": "u", "password": "p" }`.

Messages
- `GET /messages` — list messages for the authenticated user. Requires Authorization header.
- `POST /messages` — send a message. Typical payload includes `content` and either `recipient_id` or `group_id`.

Groups
- `GET /groups` — list groups.
- `GET /groups/my` — list groups for the authenticated user.
- `POST /groups` — create a group.
- `POST /groups/{id}/join` — request to join a group.
- `GET /groups/{id}/messages` — get group history.

Realtime
- `GET /stream` — SSE endpoint. Requires `Authorization: Bearer <token>` header. Response `Content-Type: text/event-stream`.

---

## Environment variables used by the server

- `DATABASE_URL` — SQLAlchemy connection string. Examples:
  - Local sqlite: `sqlite:///./messenger.db`
  - Postgres: `postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`
- `ALLOWED_ORIGINS` — comma-separated origins for CORS (e.g. `http://localhost:5173,https://app.example.com`).
- `PORT` — optional port used by the `Procfile` or container runtime.

---

## Exact commands — local development

Backend (PowerShell commands):

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
# run server with sqlite
$env:DATABASE_URL = 'sqlite:///./messenger.db'
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (PowerShell):

```powershell
cd client-app
npm install
npm run dev
```

Build frontend with production API base URL:

```powershell
cd client-app
VITE_API_URL=https://api.example.com/ npm run build
```

Docker — build and run backend container:

```powershell
docker build -t secure-messenger:latest .
docker run -e DATABASE_URL="sqlite:///./messenger.db" -p 8000:8000 secure-messenger:latest
```

Alembic migrations (run where `alembic` is available and `DATABASE_URL` is set):

```powershell
alembic upgrade head
```

---

## Notes on realtime (SSE) implementation

- The backend publishes message events to an in-process `broadcaster` when messages are created.
- The `/stream` endpoint subscribes to the broadcaster and sends matching events to the connected client as SSE (`text/event-stream`).
- For horizontal scaling, a central broker (Redis Pub/Sub or similar) is required so events published on one instance are received by subscribers connected to other instances.

---

## Minimal troubleshooting

- If the backend cannot connect to the DB: confirm `DATABASE_URL`, network access, and DB credentials.
- If `psycopg2` fails to install on some platforms: either install OS-level libpq headers or use `psycopg2-binary` in `requirements.txt`.
- If SSE appears buffered by a proxy: verify load balancer/reverse proxy streaming config.

---

If specific sections must be expanded into exact request/response examples or the full API JSON schemas, list which endpoints you want expanded and the README will be updated with those exact examples.
  - `server/services/` — business logic for auth, messages, groups.
  - `server/repositories/` — DB access wrappers.
- `migrations/` and `alembic.ini` — Alembic migration scripts and configuration.
- `client-app/` — React + Vite frontend
  - `client-app/src/api.js` — central API client; uses `import.meta.env.VITE_API_URL || '/'`.
  - `client-app/src/pages/Chat.jsx` — chat UI, message list and input, SSE integration.
  - `client-app/src/pages/Login.jsx`, `Register.jsx` — auth pages.
- `requirements.txt` — Python dependencies.
- `pyproject.toml` — optional project metadata.
- `Dockerfile`, `.dockerignore` — container build files.
- `Procfile` — process command for Procfile-based platforms.

---

## API endpoints (concise reference)

Auth
- `POST /register` — register a new user. Example payload: `{ "username": "u", "password": "p", "email": "e" }`.
- `POST /login` — authenticate and receive JWT access token. Example payload: `{ "username": "u", "password": "p" }`.

Messages
- `GET /messages` — list messages for the authenticated user. Requires Authorization header.
- `POST /messages` — send a message. Typical payload includes `content` and either `recipient_id` or `group_id`.

Groups
- `GET /groups` — list groups.
- `GET /groups/my` — list groups for the authenticated user.
- `POST /groups` — create a group.
- `POST /groups/{id}/join` — request to join a group.
- `GET /groups/{id}/messages` — get group history.

Realtime
- `GET /stream` — SSE endpoint. Requires `Authorization: Bearer <token>` header. Response `Content-Type: text/event-stream`.

---

## Environment variables used by the server

- `DATABASE_URL` — SQLAlchemy connection string. Examples:
  - Local sqlite: `sqlite:///./messenger.db`
  - Postgres: `postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`
- `ALLOWED_ORIGINS` — comma-separated origins for CORS (e.g. `http://localhost:5173,https://app.example.com`).
- `PORT` — optional port used by the `Procfile` or container runtime.

---

## Exact commands — local development

Backend (PowerShell commands):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# run server with sqlite
$env:DATABASE_URL = 'sqlite:///./messenger.db'
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (PowerShell):

```powershell
cd client-app
npm install
npm run dev
```

Build frontend with production API base URL:

```powershell
cd client-app
VITE_API_URL=https://api.example.com/ npm run build
```

Docker — build and run backend container:

```powershell
docker build -t secure-messenger:latest .
docker run -e DATABASE_URL="sqlite:///./messenger.db" -p 8000:8000 secure-messenger:latest
```

Alembic migrations (run where `alembic` is available and `DATABASE_URL` is set):

```powershell
alembic upgrade head
```

---

## Notes on realtime (SSE) implementation

- The backend publishes message events to an in-process `broadcaster` when messages are created.
- The `/stream` endpoint subscribes to the broadcaster and sends matching events to the connected client as SSE (`text/event-stream`).
- For horizontal scaling, a central broker (Redis Pub/Sub or similar) is required so events published on one instance are received by subscribers connected to other instances.

---

## Minimal troubleshooting

- If the backend cannot connect to the DB: confirm `DATABASE_URL`, network access, and DB credentials.
- If `psycopg2` fails to install on some platforms: either install OS-level libpq headers or use `psycopg2-binary` in `requirements.txt`.
- If SSE appears buffered by a proxy: verify load balancer/reverse proxy streaming config.

---

If specific sections must be expanded into exact request/response examples or the full API JSON schemas, list which endpoints you want expanded and the README will be updated with those exact examples.
- The endpoint returns a `StreamingResponse` with `text/event-stream` and headers that prevent buffering by reverse proxies.
