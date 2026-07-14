# Import create_engine to establish a connection with PostgreSQL
from sqlalchemy import create_engine

# Import sessionmaker to create database sessions
# Import declarative_base to create SQLAlchemy models later
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from the .env file
from dotenv import load_dotenv

# os helps us read environment variables like DATABASE_URL
import os


# -------------------------------------------------------
# STEP 1: Load all environment variables from the .env file
# -------------------------------------------------------
# Without this, Python cannot read DATABASE_URL.
load_dotenv()


# -------------------------------------------------------
# STEP 2: Read the DATABASE_URL from the .env file
# -------------------------------------------------------
# Example:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/smart_ticket_router
DATABASE_URL = os.getenv("DATABASE_URL")


# -------------------------------------------------------
# STEP 3: Create the SQLAlchemy Engine
# -------------------------------------------------------
# Think of the engine as a bridge between
# FastAPI and PostgreSQL.
#
# FastAPI
#     │
#     ▼
# SQLAlchemy Engine
#     │
#     ▼
# PostgreSQL
engine = create_engine(
    DATABASE_URL,
    # Checks a connection is still alive before handing it out, so a
    # connection dropped by the DB (e.g. after being idle) doesn't
    # surface as a confusing request failure.
    pool_pre_ping=True,
)


# -------------------------------------------------------
# STEP 4: Create a Session Factory
# -------------------------------------------------------
# Every time we interact with the database
# (Insert, Update, Delete, Select),
# we'll first create a session from SessionLocal.
#
# Think of a session like opening a conversation
# with the database.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# -------------------------------------------------------
# STEP 5: Create the Base Class
# -------------------------------------------------------
# Every SQLAlchemy model (table) will inherit from Base.
#
# Example:
#
# class Ticket(Base):
#     __tablename__ = "tickets"
#
# This tells SQLAlchemy that Ticket is a database table.
Base = declarative_base()

# Create a database session for each request
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()



'''
"connection.py centralizes the database configuration. 
It loads the database URL from the .env file, 
creates the SQLAlchemy engine, creates a session factory for database operations, 
and defines a base class that all SQLAlchemy models inherit from. 
This avoids duplicating connection logic throughout the project."
'''