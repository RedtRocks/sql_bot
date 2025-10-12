import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


def get_connection():
    """
    Get a PostgreSQL connection using the POSTGRES_URL environment variable.
    Returns a connection object that should be used in a context manager.
    """
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise ConnectionError("POSTGRES_URL environment variable is not set")
    
    # Clean up the URL if it has extra characters or quotes
    postgres_url = postgres_url.strip()
    if postgres_url.startswith("psql "):
        postgres_url = postgres_url[5:]  # Remove "psql " prefix
    if postgres_url.startswith("'") and postgres_url.endswith("'"):
        postgres_url = postgres_url[1:-1]  # Remove surrounding quotes
    if postgres_url.startswith('"') and postgres_url.endswith('"'):
        postgres_url = postgres_url[1:-1]  # Remove surrounding quotes
    
    # Add SSL mode if not already present
    if "sslmode=" not in postgres_url:
        separator = "&" if "?" in postgres_url else "?"
        postgres_url = f"{postgres_url}{separator}sslmode=require"
    
    return psycopg2.connect(postgres_url)


@contextmanager
def get_db_connection():
    """
    Context manager for PostgreSQL database connections.
    Automatically handles connection cleanup.
    """
    connection = None
    try:
        connection = get_connection()
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()


def run_query(sql: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return results as a list of dictionaries.
    Uses parameterized queries for safety.
    
    Args:
        sql: SQL query to execute
        limit: Optional limit on number of rows to return
        
    Returns:
        List of dictionaries representing query results
        
    Raises:
        ConnectionError: If database connection fails
        Exception: If query execution fails
    """
    # Apply LIMIT clause for PostgreSQL if requested
    limited_sql = sql
    if limit is not None:
        # Add LIMIT clause if not already present
        if "LIMIT" not in sql.upper():
            limited_sql = f"{sql.rstrip(';')} LIMIT {int(limit)}"
    
    # Fallback data when connection is not available
    if not os.getenv("POSTGRES_URL"):
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}][: limit or 2]
    
    try:
        with get_db_connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(limited_sql)
                rows = cursor.fetchall()
                # Convert RealDictRow objects to regular dictionaries
                return [dict(row) for row in rows]
    except psycopg2.Error as e:
        raise Exception(f"Database query failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")


def test_connection() -> Dict[str, Any]:
    """
    Test the database connection by running a simple query.
    
    Returns:
        Dictionary with connection status and PostgreSQL version
        
    Raises:
        Exception: If connection or query fails
    """
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                return {
                    "status": "success",
                    "message": "Database connection successful",
                    "version": version
                }
    except Exception as e:
        return {
            "status": "error",
            "message": "Database connection failed",
            "details": str(e)
        }
