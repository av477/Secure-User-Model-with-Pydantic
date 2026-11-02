# Secure User Model with Pydantic

A FastAPI service with a secure user model: a SQLAlchemy `User` table with unique
username and email, Pydantic schemas for input and output, bcrypt password hashing,
unit and integration tests, and a GitHub Actions pipeline that pushes a Docker
image to Docker Hub when the tests pass.

**Docker Hub image:** `https://hub.docker.com/r/<your-dockerhub-username>/secure-user-model`

## Features

| Requirement | Where |
|---|---|
| SQLAlchemy `User` model: `username`, `email`, `password_hash` (unique constraints) and `created_at` | [`app/models/user.py`](app/models/user.py) |
| `UserCreate` (username, email, password) and `UserRead` (no `password_hash`) | [`app/schemas/user.py`](app/schemas/user.py) |
| `hash_password()` / `verify_password()` with bcrypt | [`app/auth/security.py`](app/auth/security.py) |
| Create, look up and authenticate users | [`app/operations/users.py`](app/operations/users.py) |
| REST API | [`app/main.py`](app/main.py) |
| Unit tests (no database) | [`tests/unit/`](tests/unit) |
| Integration tests (real PostgreSQL) | [`tests/integration/`](tests/integration) |
| CI/CD (test, then push to Docker Hub) | [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) |

### Security choices
- Passwords are hashed with **bcrypt** and a random salt; the plain-text password is never stored or returned.
- `UserRead` contains only `id`, `username`, `email` and `created_at`, so the hash can't leak through the API.
- Passwords need at least 8 characters, an uppercase letter, a lowercase letter and a digit. Passwords over bcrypt's 72-byte limit are rejected rather than silently truncated.
- Usernames and emails are stored in lowercase, so `Alice@Example.com` and `alice@example.com` count as the same account.
- Uniqueness is enforced by the database's `UNIQUE` constraints; the API turns a violation into **409 Conflict**.
- The Docker image runs as a non-root user.

## API

| Method | Path | Description | Responses |
|---|---|---|---|
| `GET` | `/health` | Health check | 200 |
| `POST` | `/users` | Register a user (`UserCreate`) | 201, 409 duplicate, 422 invalid input |
| `GET` | `/users/{id}` | Get a user (`UserRead`) | 200, 404 |
| `POST` | `/users/verify` | Check a username/email and password | 200, 401 |

Interactive docs: `http://localhost:8000/docs`

## Run with Docker Compose

```bash
docker compose up --build
```

This starts PostgreSQL 17 and the API on `http://localhost:8000`. If ports 5432 or 8000 are already in use, choose others:

```bash
DB_PORT=5434 API_PORT=8001 docker compose up --build
```

## Run the tests locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Unit tests need no database
pytest tests/unit

# Integration tests need PostgreSQL
docker run -d --name test-db -e POSTGRES_USER=ci_user -e POSTGRES_PASSWORD=ci_password \
  -e POSTGRES_DB=ci_users -p 5433:5432 postgres:17
export DATABASE_URL=postgresql+psycopg2://ci_user:ci_password@localhost:5433/ci_users
pytest tests/integration --cov=app --cov-report=term-missing
```

The integration tests drop and recreate the `users` table, so point `DATABASE_URL` at a test database only. Each test runs inside a transaction that is rolled back afterwards, so tests don't affect one another.

**What is tested**
- *Unit:* hashing produces salted bcrypt hashes; verification accepts the right password and rejects wrong, empty or malformed input; schema validation of emails, usernames, password strength and missing fields; `UserRead` never exposes the hash.
- *Integration:* the hash (not the password) is stored in PostgreSQL; `created_at` is set by the database; duplicate username/email are rejected, including by the raw table constraint; the API returns 201, 409, 422, 404 and 401 as expected, and no response contains `password_hash`.

## CI/CD

On every push and pull request to `main`, GitHub Actions:
1. **Test:** starts a PostgreSQL 17 service container, installs dependencies, and runs the unit tests and then the integration tests with coverage.
2. **Deploy** (pushes to `main` only, after the tests pass): builds the image and pushes it to Docker Hub as `secure-user-model:latest` and `secure-user-model:<commit-sha>`.

### Setup
1. On Docker Hub, create an access token (**Account settings → Personal access tokens**, with *Read & Write* access).
2. In the GitHub repository, go to **Settings → Secrets and variables → Actions** and add:
   - `DOCKERHUB_USERNAME`: your Docker Hub username
   - `DOCKERHUB_TOKEN`: the access token
3. Push to `main` and watch the **Actions** tab.

Pull the published image:

```bash
docker pull <your-dockerhub-username>/secure-user-model:latest
```

## Project structure

```
app/
  auth/
    security.py  bcrypt hash_password / verify_password
  models/
    user.py      SQLAlchemy User model
  operations/
    users.py     create / get / authenticate users
  schemas/
    user.py      Pydantic UserCreate / UserRead / UserLogin
  config.py      settings from environment variables
  database.py    engine, session factory, declarative Base
  main.py        FastAPI routes
tests/
  unit/          hashing and schema tests
  integration/   PostgreSQL model and API tests
.github/workflows/ci-cd.yml
Dockerfile
docker-compose.yml
```
