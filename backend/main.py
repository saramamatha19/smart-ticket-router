# Used for application-wide logging configuration
import logging
from contextlib import asynccontextmanager

# Import FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Import database engine
from app.database.connection import engine
from app.database.init_db import create_tables

# Import API routers
from app.router.routes import router
from app.router.auth_routes import router as auth_router
from app.router.customer_routes import router as customer_router

# Configure logging once, at process startup. Every module gets its
# own named logger via logging.getLogger(__name__) and inherits this
# configuration.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # There's no migration tool in this project -- create_all() only
    # creates tables that don't exist yet (e.g. the new `customers`
    # table), it won't add a column to an already-existing `tickets`
    # table, so that one extra column is added by hand here. Both
    # statements are idempotent and safe to run on every startup.
    create_tables()
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE tickets "
                "ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(id)"
            )
        )
    yield


# Create FastAPI app
app = FastAPI(
    title="Smart Ticket Router API",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow React frontend to access the backend
app.add_middleware(
    CORSMiddleware,

    # React app URL
    allow_origins=["http://localhost:5173"],

    # Allow cookies if needed
    allow_credentials=True,

    # The frontend only ever makes GET and POST requests
    allow_methods=["GET", "POST"],

    # The frontend sends JSON bodies, plus a bearer token on admin requests
    allow_headers=["Content-Type", "Authorization"],
)

# Include all API routes
app.include_router(router)
app.include_router(auth_router)
app.include_router(customer_router)


# Home API
@app.get("/")
def home():
    return {
        "message": "Smart Ticket Router API is Running"
    }


# Test Database API
@app.get("/test-db")
def test_db():

    try:

        connection = engine.connect()

        connection.close()

        return {
            "status": "success",
            "message": "Database Connected Successfully!"
        }

    except Exception:

        # Log the full detail server-side; never expose raw connection
        # errors (which can include hostnames/credentials) to a caller.
        logging.getLogger(__name__).error("Database connectivity check failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Database is not reachable.")