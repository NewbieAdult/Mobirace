from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

username = "mobirace"
password = "Mobirace@123"
host = "hcm.mobifone.vn"
port = "8306"
database_name = "mobirace"
encoded_password = quote_plus(password)
# SQLALCHEMY_DATABASE_URL = "mysql://root:w3KzZL1Gt8gheqcMGQld@containers-us-west-160.railway.app:8306/company"
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{username}:{encoded_password}@{host}:{port}/{database_name}"

engine=create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False,bind=engine)

Base = declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()