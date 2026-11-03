from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import configure_logging
from app.database.session import get_db
from app.middleware.cors import add_cors
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import auth, categories, jobs, notifications, providers, quotes, reviews, users, websocket

configure_logging()

app = FastAPI(title="Service Marketplace API")
add_cors(app)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(jobs.router)
app.include_router(notifications.router)
app.include_router(providers.router)
app.include_router(quotes.router)
app.include_router(reviews.router)
app.include_router(users.router)
app.include_router(websocket.router)


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
