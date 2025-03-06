import asyncio
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from logging_config import setup_logger

logger = setup_logger(__name__)

load_dotenv()

_POSTGRES_HOST = os.getenv("localhost")
_POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
_POSTGRES_USER = os.getenv("POSTGRES_USER")
_POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
_POSTGRES_DB = os.getenv("POSTGRES_DB")


class DatabaseConnection:
    def __init__(self):
        self.conn = None

    async def connect(self, retry_interval=5, max_retries=None):
        """Establish a connection to the PostgreSQL database.

        For testing, you can limit retries by passing max_retries.
        """
        retries = 0
        while self.conn is None:
            try:
                self.conn = psycopg2.connect(
                    host=_POSTGRES_HOST,
                    port=_POSTGRES_PORT,
                    user=_POSTGRES_USER,
                    password=_POSTGRES_PASSWORD,
                    database=_POSTGRES_DB,
                )
                logger.info("Connected to PostgreSQL successfully.")
            except psycopg2.Error as e:
                logger.error(
                    f"Failed to connect to PostgreSQL: {str(e)}. Retrying in {retry_interval} seconds..."
                )
                self.conn = None
                retries += 1
                if max_retries is not None and retries >= max_retries:
                    break
                await asyncio.sleep(retry_interval)

        if self.conn:
            self.conn.autocommit = True

    async def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("PostgreSQL connection closed.")

    async def execute_query(self, query, *args):
        """Execute a SQL query on the database.

        Returns:
            list: The result of the query (if any) or None.
        """
        if not self.conn:
            logger.error("Database not connected.")
            return None

        cursor = None
        try:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(query, args)
            if cursor.description:
                result = cursor.fetchall()
                return [dict(row) for row in result]
            else:
                return None
        except psycopg2.Error as e:
            logger.error(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def is_connected(self):
        """Check if the database is connected."""
        return self.conn is not None and not self.conn.closed


db_connection = DatabaseConnection()
__all__ = ["db_connection"]
