from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus

# Exemplo: Conexão via IP para MySQL
user = "falconcore"
password = quote_plus("f@lc0nc0r3")  # escapa o @
host = "10.8.28.67"
db = "dbfalconcore"

DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:3306/{db}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()