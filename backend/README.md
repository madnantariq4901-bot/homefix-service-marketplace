# Service Marketplace Backend (Ubuntu)

FastAPI + SQLAlchemy + PostgreSQL + Alembic.

From this `backend` directory:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
```

Set `DATABASE_URL` to your local PostgreSQL `service_marketplace` database and replace `JWT_SECRET` with a private random value. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` if you want to seed an administrator account.
For production, set `ENVIRONMENT=production`; the API refuses to start with the development JWT secret or a secret shorter than 32 characters.

Password reset emails require `SMTP_HOST` and `SMTP_FROM_EMAIL`; configure SMTP credentials with `SMTP_USERNAME` and `SMTP_PASSWORD` when required by your provider. `SMTP_PORT` defaults to 587 and `SMTP_USE_TLS` defaults to true. Set `FRONTEND_BASE_URL` to the public frontend origin so reset links point to the deployed site. Reset links expire after `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` (60 by default).

The local demo provider accounts are `cleaner@example.com`, `plumber@example.com`, and `electrician@example.com`; each uses password `DemoProvider123`. Maryam Hassan is the cleaner account. Run `python seed.py` to create or migrate the demo accounts and add matching open sample jobs. Older seeded `@demo.local` provider addresses are migrated to the valid `@example.com` addresses when there is no conflicting account.

For a new, empty database only, run:

```bash
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

When updating an existing installation, install the current requirements and apply pending migrations before restarting the API:

```bash
python -m pip install -r requirements.txt
alembic upgrade head
```

The migration history supports databases previously stamped at `0004_review_experience`; upgrading from that revision also creates the password-reset token table.

API docs: http://127.0.0.1:8000/docs
Database health: http://127.0.0.1:8000/health/database

Do not run the initial migration against a database with existing tables until you have backed it up and compared its schema. Keep `.env` private. This is a local development setup; test and harden the app before public deployment.

Provider identity uploads are stored under `backend/private_uploads/` by default with restrictive filesystem permissions, and the directory is excluded from version control. Set `IDENTITY_UPLOAD_DIR` to a private persistent directory in `.env` when needed. Providers must submit front/back ID images and a live camera selfie before quoting; camera capture requires a secure browser context (HTTPS in production). The app does not automatically authenticate government IDs. The marketplace badge is awarded after five jobs are completed and confirmed by their customers, or can be managed by an administrator; it does not mean an ID has been authenticated. Customers receive in-app notifications when their provider is on the way and when the provider requests completion. Providers only receive a customer's exact address and coordinates after a quote is accepted. Before public deployment, implement controlled ID review, encrypted private storage, retention/deletion controls, privacy consent, and secure token handling. 
