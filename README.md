# Secure Messenger

Project summary
---------------
Secure Messenger is a small educational chat app demonstrating a REST API (FastAPI) with realtime server→client updates (SSE). It includes JWT authentication, direct and group messaging, and database migrations via Alembic.
- `Dockerfile`, `.dockerignore` — container build files.
- `Procfile` — process command for Procfile-based platforms.

---

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

AWS deployment (RDS + Secrets Manager) — quick guide
-------------------------------------------------

This project can run against an AWS RDS Postgres instance. The high-level steps are:

- Create an RDS Postgres instance in your desired AWS region. Note the endpoint (HOST), port (usually 5432), database name (DBNAME), username and password.
- Create a secret in AWS Secrets Manager (or SSM Parameter Store) to store the DB credentials and any JWT secrets. Store either the full SQLAlchemy DATABASE_URL or the individual fields.
- In your deployment environment (ECS task, Elastic Beanstalk, App Runner, EC2), set the environment variables the app expects:
	- `DATABASE_URL` — SQLAlchemy connection string, example:
		`postgresql+psycopg2://user:pass@host:5432/dbname`
	- `ALLOWED_ORIGINS` — comma-separated allowed CORS origins (e.g. `https://your-frontend.example.com`)
	- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT config used by `server/core/auth.py` (if not set, the app may fail at startup)

- Security groups / networking: ensure the RDS instance's security group allows inbound connections from the network where your app runs (for example the ECS/EB security group or VPC CIDR). If your app runs in the same VPC, prefer referencing the app's security group in the RDS inbound rule.

- Use IAM roles for your compute environment (ECS task role, EC2 instance role, EB instance profile) to grant access to Secrets Manager so your app can fetch secrets at runtime. Alternatively, inject the env vars at deployment time from your CI/CD pipeline.

AWS CLI example snippets (replace placeholders):

1) Create a simple secret containing the DATABASE_URL (Secrets Manager):

aws secretsmanager create-secret --name secure-messenger/db --secret-string '{"DATABASE_URL":"postgresql+psycopg2://user:pass@host:5432/dbname"}' --region us-east-1

2) When configuring your ECS Task Definition / Elastic Beanstalk environment, set the `DATABASE_URL` env var from the secret or point your app's startup script to retrieve it from Secrets Manager.

Notes and recommendations
- Add `psycopg2-binary==2.9.6` to `requirements.txt` (done) so the runtime can connect to Postgres without needing system build deps. If you prefer `psycopg2`, ensure the build image includes libpq-dev and Python headers.
- Store sensitive values (DB password, SECRET_KEY) in Secrets Manager or Parameter Store rather than plaintext env vars in your repo.
- Make sure to run Alembic migrations after deploying so the database schema is up-to-date. You can run migrations as a pre-start step in your container or via a CI job.

Design decisions & trade-offs
---------------------------

This section explains the rationale behind the main technology choices in the project and known trade-offs. It documents what a production deployment should change or improve.

- Why bcrypt for password hashing
	- bcrypt is a proven, memory- and CPU‑bound password hash designed to slow offline brute‑force attacks. It provides an adjustable cost factor so you can increase work as hardware improves. Avoid fast hashes (SHA256, MD5) for passwords because they're too cheap for attackers.

- Why AES‑GCM (authenticated encryption) instead of AES‑CBC
	- AES‑GCM provides authenticated encryption: confidentiality and integrity in one primitive. That means ciphertext tampering is detected automatically. AES‑CBC requires additional authentication (HMAC) to safely detect tampering and is more error‑prone if implemented incorrectly. GCM is also efficient and widely supported. The main trade‑off is careful nonce management — never reuse a nonce with the same key.

- Why SSE (Server‑Sent Events) over WebSockets
	- SSE is a simple HTTP-based mechanism for server→client streaming with automatic reconnection and is easy to proxy and scale for one‑way notifications. This project only needs server→client updates for most flows, so SSE keeps the implementation and auth model simpler. WebSockets are better for full duplex, low‑latency two‑way interactions but add complexity (connection lifecycle, proxying, sticky sessions). If you need two‑way chat or very high throughput, consider switching to WebSockets or a dedicated messaging layer.

- What breaks on server restart (and why)
	- The in‑process broadcaster keeps subscriber queues and any in‑memory state inside the running process. On restart or when scaling to multiple instances those in‑memory queues are lost and active SSE connections drop. To avoid lost events in production you must replace the in‑process broadcaster with an external pub/sub (Redis, NATS, Kafka) and use graceful connection draining when rolling restarts.

- Production checklist (short)
	- Use Postgres or another production RDBMS (not SQLite) and run Alembic migrations as part of deployment.
	- Replace the in‑process broadcaster with Redis pub/sub (or another message broker) to support multiple instances and durable delivery where needed.
	- Store secrets in a managed service (Secrets Manager, Vault) and rotate them.
	- Configure logging, monitoring and alerting; use structured logs or a log aggregator for production traces.
	- Add graceful shutdown / connection draining in front of rolling deploys to reduce dropped SSE connections.


Client / frontend notes
- The frontend reads `VITE_API_URL` at build time (see `client-app/src/api.js`). When building your production frontend, set `VITE_API_URL=https://api.yourdomain.com` so the compiled JS points to the production API.

Example environment variables to configure in production

- `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname`
- `ALLOWED_ORIGINS=https://your-frontend.example.com`
- `SECRET_KEY=<your-jwt-secret>`
- `ALGORITHM=HS256` (or your chosen algorithm)
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`

If you'd like, I can prepare:
- AWS CLI commands / CloudFormation or Terraform snippets to create the RDS instance and Secrets Manager secret.
- A small startup script that fetches secrets from Secrets Manager and exports them as env vars before running `uvicorn`.

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

Security notes (login enumeration / timing oracle)
-----------------------------------------------

- The authentication flow mitigates timing-oracle user enumeration by performing a
	bcrypt check even when a username is not found, reducing the time difference
	between "unknown user" and "wrong password" responses. This makes it harder
	for attackers to enumerate valid usernames via timing measurements.
- Rate-limit the `/login` endpoint in production (IP and account based) to
	prevent brute-force and enumeration attacks. Use a reverse-proxy or API
	gateway (e.g., AWS ALB, Cloudflare, Nginx) or an application middleware to
	enforce throttling.



