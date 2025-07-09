from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Remote MySQL credentials (freesqldatabase.com)
host = 'sql12.freesqldatabase.com'
database = 'sql12789129'
user = 'sql12789129'
password = 'X6vDclUeNr'
port = '3306'

# SQLAlchemy engine with PyMySQL
DATABASE_URL = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
engine = create_engine(DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

