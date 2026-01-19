# utils/db_connection.py

import psycopg2
from dotenv import load_dotenv, find_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    logger.warning(".env file not found. Using environment variables.")

DB_SCHEMA = os.getenv("DB_SCHEMA", "more_house")


def get_db_connection():
    """
    Establishes and returns a new database connection using psycopg2.
    Sets the search_path to the more_house schema.
    """
    try:
        TIMESCALE_SERVICE_URL = os.getenv("TIMESCALE_SERVICE_URL")
        if not TIMESCALE_SERVICE_URL:
            raise EnvironmentError("TIMESCALE_SERVICE_URL not set in environment.")

        logger.info("Connecting to TimescaleDB...")
        connection = psycopg2.connect(dsn=TIMESCALE_SERVICE_URL)

        # Set schema search path
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {DB_SCHEMA}, public;")
        connection.commit()

        logger.info(f"Connected. Schema: {DB_SCHEMA}")
        return connection

    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


def execute_query(query: str, params: tuple = None, fetch: bool = True):
    """
    Execute a query and optionally fetch results.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                return [dict(zip(columns, row)) for row in results]
            else:
                conn.commit()
                return cursor.rowcount
    finally:
        conn.close()
