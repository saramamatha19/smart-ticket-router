# Import create_engine to establish a connection with PostgreSQL
from sqlalchemy import create_engine

# Import sessionmaker to create database sessions
# Import declarative_base to create SQLAlchemy models later
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from the .env file
from dotenv import load_dotenv

# os helps us read environment variables like DATABASE_URL
import os

# STEP 1: Load all environment variables from the .env file
# Without this, Python cannot read DATABASE_URL.
load_dotenv()

# STEP 2: Read the DATABASE_URL from the .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# STEP 3: Create the SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    #To use the connection pool, we need to set pool_pre_ping=True. 
    # This will check if the connection is still alive before using it.   
    pool_pre_ping=True,
)

# STEP 4: Create a Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    #Don't save automatically.
    autoflush=False,
    #Don't automatically push pending changes before queries.
    bind=engine
    #use this database enine for all sessions
)

# STEP 5: Create the Base Class
Base = declarative_base()

# Create a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

