from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import re
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.azure_openai_service import AzureOpenAIService
from database.postgres_connection import run_query, test_connection
from utils.jwt_handler import jwt_required
from models import increment_column_usage, get_user_by_username, log_chat_message, log_query, get_chat_messages, save_chat_session, get_chat_sessions, get_chat_session, delete_chat_session

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def validate_sql_is_select(sql: str) -> bool:
    """Validate that SQL starts with SELECT (case-insensitive)."""
    # Strip comments and whitespace
    cleaned_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)  # Remove line comments
    cleaned_sql = re.sub(r'/\*.*?\*/', '', cleaned_sql, flags=re.DOTALL)  # Remove block comments
    cleaned_sql = cleaned_sql.strip()
    
    # Check if first non-whitespace token is SELECT
    first_token = cleaned_sql.split()[0].lower() if cleaned_sql.split() else ""
    return first_token == "select"


def extract_table_names_from_schema(schema: str) -> List[str]:
    """Extract table names from schema DDL."""
    if not schema:
        return []
    
    # Look for CREATE TABLE statements
    table_patterns = [
        r'CREATE\s+TABLE\s+(\w+)',
        r'create\s+table\s+(\w+)',
        r'TABLE\s+(\w+)',
        r'table\s+(\w+)'
    ]
    
    tables = set()
    for pattern in table_patterns:
        matches = re.findall(pattern, schema, re.IGNORECASE)
        tables.update(matches)
    
    return list(tables)


def validate_sql_references_schema(sql: str, schema: str) -> bool:
    """Validate that SQL references at least one table from the user's schema."""
    if not schema:
        return False
    
    schema_tables = extract_table_names_from_schema(schema)
    if not schema_tables:
        return False
    
    sql_lower = sql.lower()
    return any(table.lower() in sql_lower for table in schema_tables)


class GenerateSqlRequest(BaseModel):
    prompt: str = Field(...)
    userId: Optional[str] = None
    user_schema: Optional[str] = Field(None, alias="schema")


class GenerateSqlResponse(BaseModel):
    sql: str
    explain: str


class RunQueryRequest(BaseModel):
    sql: str
    limit: Optional[int] = None


class RunQueryResponse(BaseModel):
    status: str
    rows: List[Dict[str, Any]]


@router.post("/generate-sql", response_model=GenerateSqlResponse)
@limiter.limit("30/minute")  # Allow 30 requests per minute per IP
async def generate_sql(request: Request, body: GenerateSqlRequest, user=Depends(jwt_required)):
    print("=== DEBUG: generate_sql endpoint called ===")
    try:
        username = user.get("sub", "unknown")
        
        # Get user from database to access their schema
        db_user = get_user_by_username(username)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # For admin users, use admin_schema if available, otherwise use regular schema
        if db_user.role == "admin" and db_user.admin_schema:
            user_schema = db_user.admin_schema
        else:
            user_schema = db_user.schema
        
        # Check if user has a schema
        if not user_schema or user_schema.strip() == "":
            log_chat_message(username, "user", body.prompt)
            log_chat_message(username, "assistant", "Please contact your administrator to upload a database schema before using the chat. You need a schema to generate SQL queries.")
            raise HTTPException(
                status_code=400, 
                detail="Please contact your administrator to upload a database schema before using the chat. You need a schema to generate SQL queries."
            )
        
        # Log user message
        log_chat_message(username, "user", body.prompt)
        
        # Generate SQL using Azure OpenAI
        ai = AzureOpenAIService()
        try:
            sql = await ai.generate_sql(body.prompt, user_schema)
        except ValueError as e:
            if "I_CANNOT_GENERATE_SQL" in str(e):
                # Log assistant response
                log_chat_message(username, "assistant", "Your query does not match any tables in your database schema. Please ask about specific tables or columns.")
                raise HTTPException(
                    status_code=400, 
                    detail="Your query does not match any tables in your database schema. Please ask about specific tables or columns."
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to generate SQL")
        
        # Validate SQL is SELECT only
        if not validate_sql_is_select(sql):
            log_chat_message(username, "assistant", "Generated SQL is not a SELECT. For safety only SELECT queries are allowed.")
            raise HTTPException(
                status_code=400, 
                detail="Generated SQL is not a SELECT. For safety only SELECT queries are allowed."
            )
        
        # Validate SQL references user's schema (skip for admin users without schema)
        if user_schema and not validate_sql_references_schema(sql, user_schema):
            log_chat_message(username, "assistant", "The prompt did not reference your database schema. Please ask a question that mentions your tables/columns.")
            raise HTTPException(
                status_code=400, 
                detail="The prompt did not reference your database schema. Please ask a question that mentions your tables/columns."
            )
        
        # Log assistant response with generated SQL
        log_chat_message(username, "assistant", f"Here is a proposed SQL query: {sql}", sql)
        
        # Extract columns for usage logging
        cols = []
        try:
            select_part = sql.lower().split("select", 1)[1].split("from", 1)[0]
            cols = [c.strip().split(" as ")[0] for c in select_part.split(',') if c.strip() and c.strip() != '*']
        except Exception:
            cols = []
        increment_column_usage(username, cols)
        
        return {"sql": sql, "explain": "SQL generated based on your database schema"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-query", response_model=RunQueryResponse)
def run_query_endpoint(body: RunQueryRequest, user=Depends(jwt_required)):
    try:
        username = user.get("sub", "unknown")
        
        # Validate SQL is SELECT only (double check)
        if not validate_sql_is_select(body.sql):
            log_query(username, body.sql, "error", error_message="Non-SELECT query rejected")
            raise HTTPException(
                status_code=400, 
                detail="Only SELECT queries are allowed for safety"
            )
        
        # Execute query
        rows = run_query(body.sql, limit=body.limit)
        
        # Log successful query
        log_query(username, body.sql, "ok", rows_affected=len(rows))
        
        return {"status": "ok", "rows": rows}
    except HTTPException:
        raise
    except Exception as e:
        # Log failed query
        username = user.get("sub", "unknown")
        log_query(username, body.sql, "error", error_message=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry-query")
def retry_query():
    return {"status": "ok", "sql": "SELECT 2;"}


@router.get("/chat-history")
def get_chat_history(user=Depends(jwt_required)):
    """Get chat history for the current user."""
    try:
        username = user.get("sub", "unknown")
        messages = get_chat_messages(username, limit=50)  # Get last 50 messages
        return {"status": "ok", "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-session")
def save_session(session_data: dict, user=Depends(jwt_required)):
    """Save a chat session for the current user."""
    try:
        username = user.get("sub", "unknown")
        session_name = session_data.get("session_name", f"Chat {len(session_data.get('messages', []))} messages")
        messages = session_data.get("messages", [])
        
        session_id = save_chat_session(username, session_name, messages)
        return {"status": "ok", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat-sessions")
def get_sessions(user=Depends(jwt_required)):
    """Get all chat sessions for the current user."""
    try:
        username = user.get("sub", "unknown")
        sessions = get_chat_sessions(username, limit=50)
        return {"status": "ok", "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat-session/{session_id}")
def get_session(session_id: int, user=Depends(jwt_required)):
    """Get a specific chat session."""
    try:
        username = user.get("sub", "unknown")
        session = get_chat_session(session_id, username)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "ok", "session": session}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat-session/{session_id}")
def delete_session(session_id: int, user=Depends(jwt_required)):
    """Delete a chat session."""
    try:
        username = user.get("sub", "unknown")
        success = delete_chat_session(session_id, username)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "ok", "message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-db")
def test_db():
    """
    Test database connection by running SELECT version() and returning the result.
    This endpoint doesn't require authentication for testing purposes.
    """
    try:
        result = test_connection()
        return result
    except Exception as e:
        return {"error": "Database connection failed", "details": str(e)}


