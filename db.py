import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SECURITY FIX: Load all credentials from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

# SSL cert path from env var so it works on any machine
SSL_CA = os.environ.get("DB_SSL_CA", "")

connect_args = {}
if SSL_CA:
    connect_args["ssl"] = {"ca": SSL_CA}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()