import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv("api.env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in api.env")

SSL_CA = os.environ.get("DB_SSL_CA", "")

connect_args = {}
if SSL_CA:
    connect_args["ssl"] = {"ca": SSL_CA}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
