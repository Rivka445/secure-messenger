# Secure Messenger

# Secure Messenger

Project summary
---------------
Secure Messenger is a small educational chat app demonstrating a REST API (FastAPI) with realtime server→client updates (SSE). It includes JWT authentication, direct and group messaging, and database migrations via Alembic.
- `Dockerfile`, `.dockerignore` — container build files.
- `Procfile` — process command for Procfile-based platforms.

---

## API endpoints (concise reference)

Auth
- `POST /register` — register a new user. Example payload: `{ "username": "u", "password": "p", "email": "e" }`.
- `POST /login` — authenticate and receive JWT access token. Example payload: `{ "username": "u", "password": "p" }`.

# Secure Messenger

Secure Messenger is a small educational chat application that demonstrates a simple, secure messaging backend and a single-page frontend. It is intended for learning and experimentation.

Key features
------------

- JWT-based authentication
- Direct and group messages
- Realtime server→client updates via Server-Sent Events (SSE)
- Layered backend structure (routers → services → repositories)
- Database migrations using Alembic

Repository layout
-----------------

- `server/` — FastAPI backend
	- `main.py` — application factory, CORS and startup
	- `database.py` — SQLAlchemy engine and session helpers (reads `DATABASE_URL`)
	- `routers/` — HTTP routes: auth, messages, groups, stream
	- `services/`, `repositories/`, `core/` — business logic and utilities
- `client-app/` — React + Vite single-page app
	- `src/api.js` — API client (reads `VITE_API_URL` at build time)
	- `src/pages/Chat.jsx`, `Login.jsx`, `Register.jsx` — main UI pages
- `migrations/`, `alembic.ini` — Alembic migration files
- `Dockerfile`, `.dockerignore` — optional containerization files
- `requirements.txt`, `pyproject.toml` — Python dependencies and metadata

Architecture & design
---------------------

This project follows a simple layered architecture to keep responsibilities separate and make the code easy to follow:

- Frontend (client-app): a React + Vite single-page application. It authenticates with the backend using JWT, calls REST endpoints via `src/api.js`, and connects to the SSE `/stream` endpoint to receive realtime events.

- Backend (server): FastAPI application organized into routers, services and repositories:
	- Routers translate HTTP requests into service calls and perform request validation.
	- Services implement business logic (authorization checks, composing messages, group operations).
	- Repositories encapsulate direct database access via SQLAlchemy models and sessions.

- Realtime delivery: Server-Sent Events (SSE) endpoint implemented under `routers/stream_router.py`. The project includes an in-process broadcaster for development; for multi-instance deployments replace it with a Redis-based pub/sub so instances can broadcast across process boundaries.

- Database & migrations: SQLAlchemy is used for ORM models and Alembic for schema migrations. Use `DATABASE_URL` to point to SQLite locally or to a Postgres instance in production.

- Authentication: JWT-based tokens are issued at login and required for protected endpoints and for connecting to the SSE stream.

Quick API reference
-------------------

The project exposes a REST API for auth, messaging and groups and a SSE endpoint for realtime events. Below are representative examples; consult the code for full schemas.

Auth

- POST /register
	- Body: `{ "username": "alice", "email": "alice@example.com", "password": "secret" }`
	- Success: 201 Created (user data without password)

- POST /login
	- Body: `{ "username": "alice", "password": "secret" }`
	- Success: 200 OK `{ "access_token": "<jwt>", "token_type": "bearer" }`

Messages

- GET /messages
	- Requires Authorization header. Returns messages for the authenticated user.

- POST /messages
	- Requires Authorization header.
	- Direct message example: `{ "recipient_id": 2, "content": "Hello" }`
	- Group message example: `{ "group_id": 5, "content": "Hello group" }`
	- Success: 201 Created (message object)

Groups

- GET /groups
- GET /groups/my
- POST /groups
- POST /groups/{id}/join

Realtime (SSE)

- GET /stream
	- A Server-Sent Events endpoint that streams realtime messages and events.
	- Include `Authorization: Bearer <token>` header when connecting.

Environment variables
---------------------

- `DATABASE_URL` — SQLAlchemy connection string. Examples:
	- SQLite local: `sqlite:///./messenger.db`
	- Postgres: `postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME`
- `ALLOWED_ORIGINS` — comma-separated list for CORS (e.g. `http://localhost:5173,https://app.example.com`)
- `PORT` — optional port used by hosting environment

Run locally (backend)
---------------------

Prerequisites: Python 3.11+, Node.js (for frontend)

Example (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# for local development, use SQLite
$env:DATABASE_URL = 'sqlite:///./messenger.db'
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

Run frontend (development)
--------------------------

```powershell
cd client-app
npm install
npm run dev
```

Build frontend for production (example)
--------------------------------------

```powershell
cd client-app
VITE_API_URL=https://api.example.com/ npm run build
```

Database migrations (Alembic)
----------------------------

```powershell
alembic upgrade head
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Docker (simple)
---------------

Build and run a container (example):

```powershell
docker build -t secure-messenger:latest .
docker run -e DATABASE_URL="sqlite:///./messenger.db" -p 8000:8000 secure-messenger:latest
```

Deployment notes
----------------

- For production use Postgres (set `DATABASE_URL` accordingly) and ensure `psycopg2` or `psycopg2-binary` is available.
- Replace the in-process broadcaster with Redis Pub/Sub for multi-instance SSE delivery.
- Run Alembic migrations during deployment.

Testing
-------

The repository includes a `tests/` folder with pytest-based tests. Use `pytest` to run the test suite locally. For deterministic tests that touch the database, the project uses test fixtures (see `tests/conftest.py`) to create a temporary database and override FastAPI dependencies.

Basic commands (PowerShell):

```powershell
# run all tests
pytest -q

# run a single test file
pytest tests/test_app.py -q
```

Tips
- Use the `tests/conftest.py` fixtures rather than hitting your development database.
- To run tests that need a Postgres instance, set `DATABASE_URL` to a test database and ensure migrations have been applied.



