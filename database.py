from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# We will use PostgreSQL for production but can fallback to sqlite for immediate local testing if DB URL empty
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nps.db")

engine = create_engine(
    DATABASE_URL, 
    # For sqlite, we need connect_args to prevent thread issues. Ignored by postgres.
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
