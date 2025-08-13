from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import logging
import urllib.parse

logger = logging.getLogger(__name__)

load_dotenv()

SAP_DB_HOST = os.getenv("SAP_DB_HOST", "localhost")
SAP_DB_PORT = os.getenv("SAP_DB_PORT", "1433")
SAP_DB_NAME = os.getenv("SAP_DB_NAME", "")
SAP_DB_USER = os.getenv("SAP_DB_USER", "")
SAP_DB_PASSWORD = os.getenv("SAP_DB_PASSWORD", "")

if not all([SAP_DB_NAME, SAP_DB_USER, SAP_DB_PASSWORD]):
    logger.critical("CRITICAL ERROR: SQL Server database configuration is incomplete. Please check environment variables.")
    raise ValueError("SQL Server database configuration is incomplete. Please check environment variables.")

if SAP_DB_HOST and "\\" in SAP_DB_HOST:
    server_string = SAP_DB_HOST
    if SAP_DB_PORT and SAP_DB_PORT != "1433":
        logger.warning(f"SAP_DB_PORT ({SAP_DB_PORT}) is ignored when using SQL Server instance ({SAP_DB_HOST}). Instance names cannot use explicit ports.")
else:
    server_string = f"{SAP_DB_HOST},{SAP_DB_PORT}" if SAP_DB_PORT else SAP_DB_HOST

connection_string = (
    f"mssql+pyodbc:///?odbc_connect="
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server_string};"
    f"DATABASE={SAP_DB_NAME};"
    f"UID={SAP_DB_USER};"
    f"PWD={SAP_DB_PASSWORD};"
    f"Encrypt=no;"
    f"TrustServerCertificate=yes"
)

logger.info(f"Connecting to SQL Server database: {server_string}/{SAP_DB_NAME}")
logger.info(f"Connection parameters - Server: {server_string}, Database: {SAP_DB_NAME}, User: {SAP_DB_USER}")
masked_connection_string = connection_string.replace(SAP_DB_PASSWORD, "***")
logger.info(f"Full connection string: {masked_connection_string}")

engine = create_engine(
    connection_string,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base = declarative_base()

def test_connection():
    """Test database connection"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
