from models import log_query
import time


class QueryLogger:
    def __init__(self):
        self.start_time = None
    
    def start_timer(self):
        """Start timing a query execution."""
        self.start_time = time.time()
    
    def log(self, user: str, sql: str, status: str = "ok", rows_affected: int = None, error_message: str = None):
        """Log a query execution to the database."""
        execution_time_ms = None
        if self.start_time:
            execution_time_ms = int((time.time() - self.start_time) * 1000)
        
        try:
            log_query(
                username=user,
                sql_query=sql,
                status=status,
                execution_time_ms=execution_time_ms,
                rows_affected=rows_affected,
                error_message=error_message
            )
            return True
        except Exception as e:
            print(f"Failed to log query: {e}")
            return False






