# Used for application-wide logging configuration
import logging

# Import FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import database engine
from app.database.connection import engine

# Import API router
from app.router.routes import router

# Configure logging once, at process startup. Every module gets its
# own named logger via logging.getLogger(__name__) and inherits this
# configuration.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title="Smart Ticket Router API",
    version="1.0.0"
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

    # The frontend only ever sends JSON bodies
    allow_headers=["Content-Type"],
)

# Include all API routes
app.include_router(router)


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