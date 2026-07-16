# Import SQLAlchemy engine
from app.database.connection import engine

# Import Base
from app.database.connection import Base

# Import the models. Neither is "unused" despite never being referenced
# by name below -- importing them registers their tables on
# Base.metadata, which is what create_all() actually reads.
from app.models.ticket import Ticket  # noqa: F401
from app.models.customer import Customer  # noqa: F401


def create_tables():
    """
    Create all tables in PostgreSQL.
    """
    Base.metadata.create_all(bind=engine)

    '''
    This reads all your models (like Ticket) and creates the corresponding tables in PostgreSQL if they don't already exist.
    '''
    '''
    This tells SQLAlchemy:
    "Go through every model that inherits from Base, 
    and create the corresponding tables in PostgreSQL if they don't already exist."
    '''

    '''
    ticket.py (Model)
       ↓
    init_db.py
       ↓
    Creates tables in PostgreSQL
    '''