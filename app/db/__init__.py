"""Database package."""
from .database import Database

__all__ = ['Database']

def init_db(db_url: str):
    """Initialize the database."""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session() 