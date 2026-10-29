from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime, func
from sqlalchemy.types import TypeEngine
from datetime import datetime

Base = declarative_base()

class UTCDateTime(TypeEngine):
    """Custom type for UTC datetime."""
    def process_bind_param(self, value, dialect):
        if value is not None and isinstance(value, datetime):
            return value.astimezone(None) if value.tzinfo else value
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return value.astimezone(None) if value.tzinfo else value
        return value
