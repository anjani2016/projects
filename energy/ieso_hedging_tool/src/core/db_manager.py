# src/core/db_manager.py
import os
import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger("ieso_hedging_tool." + __name__)

class DatabaseManager:
    """
    Handles connection lifecycle and SQL readers.
    Designed to fall back to a local SQLite database for development, 
    but structured to support TimescaleDB/PostgreSQL connection pooling in production.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv("DATABASE_URL", "data/ieso_cache.db")
        self.db_path = db_path
        self._initialize_local_sqlite()

    def _initialize_local_sqlite(self):
        """Initializes a local database file if PostgreSQL is not specified."""
        if not self.db_path.startswith("postgres"):
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Initialized local SQLite storage at: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Provides a database connection context."""
        if self.db_path.startswith("postgres"):
            # Placeholder for production TimescaleDB pool connection
            # import psycopg2
            # conn = psycopg2.connect(self.db_path)
            raise NotImplementedError("TimescaleDB connection pool requires active PostgreSQL credentials.")
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise e
            finally:
                conn.close()

    def execute_query(self, query, params=None):
        """Executes a non-reading query (e.g. INSERT, UPDATE)."""
        params = params or ()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def fetch_dataframe(self, query, params=None):
        """Executes a query and returns result as a pandas DataFrame."""
        import pandas as pd
        params = params or ()
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
