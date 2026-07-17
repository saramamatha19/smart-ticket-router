# Import SQLAlchemy engine
from app.database.connection import engine

# Import Base
from app.database.connection import Base

from app.models.ticket import Ticket  
from app.models.customer import Customer  


def create_tables():
    #creates all tables inherited from Base in the database
    Base.metadata.create_all(bind=engine)
