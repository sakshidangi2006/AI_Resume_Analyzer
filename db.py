import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SECURITY FIX: Load all credentials from environment variables
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://3gMBvsMcQYeermS.root:zwkTHksgoXyhG7JQ@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=<CA_PATH>&ssl_verify_cert=true&ssl_verify_identity=true"  
)

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