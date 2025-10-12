"""
Database initialization and migration for SQL Bot with Neon PostgreSQL
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Control destructive reset behavior via env var:
# Set RESET_DB_ON_STARTUP=true when you explicitly want to drop & recreate tables.
RESET_DB_ON_STARTUP = os.getenv("RESET_DB_ON_STARTUP", "false").lower() in ("1", "true", "yes")

def get_postgres_connection():
    """Get a PostgreSQL connection using the POSTGRES_URL environment variable."""
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
    
    print(f"Connecting to: {postgres_url[:50]}...")  # Show first 50 chars for debugging
    
    return psycopg2.connect(postgres_url)


def create_tables():
    """Create all required tables in the PostgreSQL database."""
    
    # Define table schemas (use IF NOT EXISTS so we won't error on existing tables)
    tables = {
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                schema TEXT,
                admin_schema TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        """,
        
        "column_usage": """
            CREATE TABLE IF NOT EXISTS column_usage (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                column_name VARCHAR(255) NOT NULL,
                count BIGINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_column_usage_username ON column_usage(username);
            CREATE INDEX IF NOT EXISTS idx_column_usage_column ON column_usage(column_name);
        """,
        
        "query_logs": """
            CREATE TABLE IF NOT EXISTS query_logs (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                sql_query TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'ok',
                execution_time_ms INTEGER,
                rows_affected INTEGER,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_query_logs_username ON query_logs(username);
            CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
        """,
        
        "chat_messages": """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                sql_generated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_chat_messages_username ON chat_messages(username);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
        """,
        
        "feedback": """
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                chat_message_id INTEGER,
                feedback_text TEXT,
                rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_feedback_username ON feedback(username);
            CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
        """,
        "chat_sessions": """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                session_name VARCHAR(255) NOT NULL,
                messages TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_username ON chat_sessions(username);
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
        """
    }
    
    connection = None
    try:
        connection = get_postgres_connection()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        with connection.cursor() as cursor:
            # Only drop tables if RESET_DB_ON_STARTUP is true (explicit)
            if RESET_DB_ON_STARTUP:
                for table_name in ["feedback", "chat_messages", "query_logs", "column_usage", "users"]:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                        print(f"CLEANUP:  Dropped existing table '{table_name}' if it existed")
                    except Exception as e:
                        print(f"WARNING:  Could not drop table '{table_name}': {e}")
            else:
                print("INFO: RESET_DB_ON_STARTUP is false - skipping DROP TABLE phase")
            
            # Create each table (IF NOT EXISTS protects existing data)
            for table_name, table_sql in tables.items():
                try:
                    print(f"Creating/ensuring table: {table_name}")
                    cursor.execute(table_sql)
                    print(f"SUCCESS: Table '{table_name}' ensured")
                except Exception as e:
                    print(f"ERROR: Error creating/ensuring table '{table_name}': {e}")
                    # Continue with other tables
            
            # Add missing columns to existing tables (migration)
            try:
                # Check if admin_schema column exists in users table
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'admin_schema'
                """)
                admin_schema_exists = cursor.fetchone()
                
                if not admin_schema_exists:
                    print("Adding admin_schema column to users table...")
                    cursor.execute("ALTER TABLE users ADD COLUMN admin_schema TEXT;")
                    print("SUCCESS: admin_schema column added to users table")
                else:
                    print("admin_schema column already exists in users table")
                    
            except Exception as e:
                print(f"WARNING: Could not add admin_schema column: {e}")
            
            # Create or replace updated_at trigger function
            try:
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)
                print("SUCCESS: Updated_at trigger function created or replaced")
                
                # Attach triggers to tables that have updated_at
                for table_name in ["users", "column_usage"]:
                    try:
                        # Drop existing trigger if exists and create fresh (safe)
                        cursor.execute(f"DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_name};")
                        cursor.execute(f"""
                            CREATE TRIGGER update_{table_name}_updated_at
                            BEFORE UPDATE ON {table_name}
                            FOR EACH ROW
                            EXECUTE PROCEDURE update_updated_at_column();
                        """)
                        print(f"SUCCESS: Updated_at trigger added to '{table_name}'")
                    except Exception as e:
                        # If trigger creation fails (e.g., table missing), warn and continue
                        print(f"WARNING: Could not create trigger for '{table_name}': {e}")
                        
            except Exception as e:
                print(f"WARNING: Could not create triggers: {e}")
                print("NOTE: Triggers skipped due to error")
            
            # Commit the changes if not using autocommit (we set autocommit, but call commit to be safe)
            try:
                connection.commit()
            except Exception:
                pass
            
            print("SUCCESS: Table creation/ensuring finished")
            
    except Exception as e:
        print(f"ERROR: Error creating tables: {str(e)}")
        raise e
    finally:
        if connection:
            connection.close()


def check_database_connection():
    """Check if the database connection is working."""
    try:
        connection = get_postgres_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"Connected to PostgreSQL: {version}")
        connection.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False


def verify_tables_exist():
    """Verify that all required tables exist in the database."""
    required_tables = ["users", "column_usage", "query_logs", "chat_messages", "feedback"]
    
    connection = None
    try:
        connection = get_postgres_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = ANY(%s);
            """, (required_tables,))
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            missing_tables = set(required_tables) - set(existing_tables)
            
            if missing_tables:
                print(f"ERROR: Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                print(f"SUCCESS: All required tables exist: {', '.join(existing_tables)}")
                return True
                
    except Exception as e:
        print(f"ERROR: Error verifying tables: {str(e)}")
        return False
    finally:
        if connection:
            connection.close()


def init_neon_database():
    """Initialize the Neon PostgreSQL database with all required tables."""
    print("Initializing SQL Bot database...")
    
    # Check database connection
    if not check_database_connection():
        print("ERROR: Cannot connect to database. Please check your POSTGRES_URL.")
        return False
    
    # Create/ensure tables
    try:
        create_tables()
        
        # Verify tables were created or already exist
        if verify_tables_exist():
            print("SUCCESS: Neon database initialized successfully!")
            return True
        else:
            print("ERROR: Database initialization failed - tables not created properly")
            return False
            
    except Exception as e:
        print(f"ERROR: Database initialization failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run initialization when script is executed directly
    success = init_neon_database()
    exit(0 if success else 1)
