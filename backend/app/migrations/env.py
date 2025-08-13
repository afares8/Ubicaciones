from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.database import Base
from app.wms.models import *

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    from dotenv import load_dotenv
    load_dotenv()
    
    SAP_DB_HOST = os.getenv("SAP_DB_HOST", "localhost")
    SAP_DB_PORT = os.getenv("SAP_DB_PORT", "1433")
    SAP_DB_NAME = os.getenv("SAP_DB_NAME", "")
    SAP_DB_USER = os.getenv("SAP_DB_USER", "")
    SAP_DB_PASSWORD = os.getenv("SAP_DB_PASSWORD", "")
    
    if SAP_DB_HOST and "\\" in SAP_DB_HOST:
        server_string = SAP_DB_HOST
    else:
        server_string = f"{SAP_DB_HOST},{SAP_DB_PORT}" if SAP_DB_PORT else SAP_DB_HOST
    
    return (
        f"mssql+pyodbc:///?odbc_connect="
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server_string};"
        f"DATABASE={SAP_DB_NAME};"
        f"UID={SAP_DB_USER};"
        f"PWD={SAP_DB_PASSWORD};"
        f"Encrypt=no;"
        f"TrustServerCertificate=yes"
    )

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
