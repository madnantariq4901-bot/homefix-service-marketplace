# Service Marketplace

A local full-stack Service Marketplace project with a FastAPI backend, PostgreSQL database, Alembic migrations, and Nuxt 4 frontend.

## 1. PostgreSQL setup on Ubuntu

Check PostgreSQL is running:

```bash
pg_lsclusters
sudo systemctl enable --now postgresql
```

Open the PostgreSQL administrator console:

```bash
sudo -u postgres psql
```

If the `marketplace_user` role does not exist, create it (replace the sample password with your own):

```sql
CREATE ROLE marketplace_user WITH LOGIN PASSWORD 'choose-a-strong-password';
```

If the role already exists, set its password instead:

```sql
ALTER ROLE marketplace_user WITH PASSWORD 'choose-a-strong-password';
```

If the `service_marketplace` database does not exist, create it:

```sql
CREATE DATABASE service_marketplace OWNER marketplace_user;
```

If the database already exists, do not create it again. Instead, run:

```sql
ALTER DATABASE service_marketplace OWNER TO marketplace_user;
GRANT ALL PRIVILEGES ON DATABASE service_marketplace TO marketplace_user;
```

Exit psql with `\q`. Do not drop or reset a database that already contains data.

## 2. Backend setup on Ubuntu

From the project root:

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
```

Set `DATABASE_URL` to the database username and password you created, for example:

```text
DATABASE_URL=postgresql+psycopg2://marketplace_user:YOUR_PASSWORD@localhost:5432/service_marketplace
```

If the password contains URL-reserved characters such as `@`, `:`, `/`, or `#`, URL-encode those characters in the URL. Replace `JWT_SECRET` with a long, random private value. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` if you want to seed an administrator account. Keep `.env` private and never commit it.

The initial Alembic migration is intended for a new, empty database. Before applying it to a database with existing tables or valuable data, back up the database and compare its schema first.

With the virtual environment active and current directory `backend`, run:

```bash
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000  
Interactive API docs: http://127.0.0.1:8000/docs  
Database health check: http://127.0.0.1:8000/health/database

## 3. Frontend setup on Ubuntu

Open a second terminal from the project root:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

Open http://localhost:3000. The frontend API base URL is configured in `frontend/.env`; the default is `http://127.0.0.1:8000`.

## 4. Tests

In the backend terminal, with the virtual environment active:

```bash
python -m pytest
```

The test suite is designed to use a separate in-memory database. The running application and Alembic migration use PostgreSQL. Resolve any failing tests or environment errors before treating the app as production-ready.

## Important

This package is a local development project, not a deployed production service. Before public deployment, configure production secrets, HTTPS, backups, logging/monitoring, and production server settings, and run the complete test suite against the target environment.
