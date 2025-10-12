from sqlalchemy import Column, Integer, String, create_engine, BigInteger, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import func
import hashlib
import hmac
import os
from dotenv import load_dotenv

load_dotenv()

# Use PostgreSQL URL from environment, fallback to SQLite for development
DATABASE_URL = os.getenv("POSTGRES_URL", "sqlite:///./app.db")

# Clean up the URL if it has extra characters or quotes
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip()
    if DATABASE_URL.startswith("psql "):
        DATABASE_URL = DATABASE_URL[5:]  # Remove "psql " prefix
    if DATABASE_URL.startswith("'") and DATABASE_URL.endswith("'"):
        DATABASE_URL = DATABASE_URL[1:-1]  # Remove surrounding quotes
    if DATABASE_URL.startswith('"') and DATABASE_URL.endswith('"'):
        DATABASE_URL = DATABASE_URL[1:-1]  # Remove surrounding quotes

# Configure engine based on database type
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL)
else:
    # SQLite fallback for development
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    schema = Column(Text, nullable=True)
    admin_schema = Column(Text, nullable=True)  # Full company DB schema for admins
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class ColumnUsage(Base):
    __tablename__ = "column_usage"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    column_name = Column(String, index=True, nullable=False)
    count = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    sql_query = Column(Text, nullable=False)
    status = Column(String, default="ok")
    execution_time_ms = Column(Integer, nullable=True)
    rows_affected = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sql_generated = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    chat_message_id = Column(Integer, nullable=True)
    feedback_text = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 rating
    created_at = Column(DateTime, default=func.current_timestamp())


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    session_name = Column(String, nullable=False)
    messages = Column(Text, nullable=True)  # JSON string of messages
    created_at = Column(DateTime, default=func.current_timestamp())


def init_db():
    Base.metadata.create_all(bind=engine)


def _hash_password(password: str, username: str) -> str:
    # Simple HMAC-SHA256 with username as key (demo only)
    return hmac.new(username.encode(), password.encode(), hashlib.sha256).hexdigest()


def verify_password(username: str, password: str, password_hash: str) -> bool:
    return hmac.compare_digest(_hash_password(password, username), password_hash)


def create_user(username: str, password: str, role: str = "user", schema: str | None = None, admin_schema: str | None = None):
    with SessionLocal() as db:
        user = User(username=username, password_hash=_hash_password(password, username), role=role, schema=schema, admin_schema=admin_schema)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def delete_user(username: str) -> bool:
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True


def get_user_by_username(username: str) -> User | None:
    with SessionLocal() as db:
        return db.query(User).filter(User.username == username).first()


def increment_column_usage(username: str, columns: list[str]):
    if not columns:
        return
    with SessionLocal() as db:
        for col in columns:
            rec = db.query(ColumnUsage).filter(ColumnUsage.username == username, ColumnUsage.column_name == col).first()
            if not rec:
                rec = ColumnUsage(username=username, column_name=col, count=0)
                db.add(rec)
            rec.count = (rec.count or 0) + 1
        db.commit()


def get_column_usage_summary() -> list[dict]:
    with SessionLocal() as db:
        rows = db.query(ColumnUsage).all()
        return [{"username": r.username, "column": r.column_name, "count": int(r.count or 0)} for r in rows]


def log_query(username: str, sql_query: str, status: str = "ok", execution_time_ms: int = None, 
              rows_affected: int = None, error_message: str = None):
    """Log a query execution to the query_logs table."""
    with SessionLocal() as db:
        query_log = QueryLog(
            username=username,
            sql_query=sql_query,
            status=status,
            execution_time_ms=execution_time_ms,
            rows_affected=rows_affected,
            error_message=error_message
        )
        db.add(query_log)
        db.commit()
        return query_log


def get_query_logs(username: str = None, limit: int = 100) -> list[dict]:
    """Get query logs, optionally filtered by username."""
    with SessionLocal() as db:
        query = db.query(QueryLog)
        if username:
            query = query.filter(QueryLog.username == username)
        
        logs = query.order_by(QueryLog.created_at.desc()).limit(limit).all()
        return [
            {
                "id": log.id,
                "username": log.username,
                "sql_query": log.sql_query,
                "status": log.status,
                "execution_time_ms": log.execution_time_ms,
                "rows_affected": log.rows_affected,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]


def log_chat_message(username: str, role: str, content: str, sql_generated: str = None):
    """Log a chat message to the chat_messages table."""
    with SessionLocal() as db:
        chat_message = ChatMessage(
            username=username,
            role=role,
            content=content,
            sql_generated=sql_generated
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        return chat_message


def get_chat_messages(username: str = None, limit: int = 500) -> list[dict]:
    """Get chat messages, optionally filtered by username."""
    with SessionLocal() as db:
        query = db.query(ChatMessage)
        if username:
            query = query.filter(ChatMessage.username == username)
        
        messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
        return [
            {
                "id": msg.id,
                "username": msg.username,
                "role": msg.role,
                "content": msg.content,
                "sql_generated": msg.sql_generated,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]


def get_feedback(username: str = None, limit: int = 500) -> list[dict]:
    """Get feedback records, optionally filtered by username."""
    with SessionLocal() as db:
        query = db.query(Feedback)
        if username:
            query = query.filter(Feedback.username == username)
        
        feedback = query.order_by(Feedback.created_at.desc()).limit(limit).all()
        return [
            {
                "id": fb.id,
                "username": fb.username,
                "chat_message_id": fb.chat_message_id,
                "feedback_text": fb.feedback_text,
                "rating": fb.rating,
                "created_at": fb.created_at.isoformat() if fb.created_at else None
            }
            for fb in feedback
        ]


def save_chat_session(username: str, session_name: str, messages: list) -> int:
    """Save a chat session for a user."""
    import json
    with SessionLocal() as db:
        # Create a new chat session record
        session = ChatSession(
            username=username,
            session_name=session_name,
            messages=json.dumps(messages),
            created_at=func.current_timestamp()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.id


def get_chat_sessions(username: str, limit: int = 50) -> list:
    """Get chat sessions for a user."""
    import json
    with SessionLocal() as db:
        sessions = db.query(ChatSession).filter(ChatSession.username == username).order_by(ChatSession.created_at.desc()).limit(limit).all()
        return [
            {
                "id": s.id,
                "username": s.username,
                "session_name": s.session_name,
                "messages": json.loads(s.messages) if s.messages else [],
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in sessions
        ]


def get_chat_session(session_id: int, username: str) -> dict:
    """Get a specific chat session."""
    import json
    with SessionLocal() as db:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.username == username).first()
        if session:
            return {
                "id": session.id,
                "username": session.username,
                "session_name": session.session_name,
                "messages": json.loads(session.messages) if session.messages else [],
                "created_at": session.created_at.isoformat() if session.created_at else None
            }
        return None


def delete_chat_session(session_id: int, username: str) -> bool:
    """Delete a chat session for a user."""
    with SessionLocal() as db:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.username == username).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False


def get_all_users() -> list:
    """Get all users for admin panel."""
    with SessionLocal() as db:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role,
                "schema": u.schema,
                "admin_schema": u.admin_schema,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]

def get_user_by_id(user_id: int) -> User:
    """Get user by ID."""
    with SessionLocal() as db:
        return db.query(User).filter(User.id == user_id).first()

def update_user_info(user_id: int, username: str = None, password: str = None, 
                    role: str = None, schema: str = None, admin_schema: str = None) -> dict:
    """Update user information."""
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Update fields if provided
        if username is not None:
            user.username = username
        if password is not None and password.strip():
            user.password_hash = hash_password(password)
        if role is not None:
            user.role = role
        if schema is not None:
            user.schema = schema
        if admin_schema is not None:
            user.admin_schema = admin_schema
        
        db.commit()
        db.refresh(user)
        
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "schema": user.schema,
            "admin_schema": user.admin_schema,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }


