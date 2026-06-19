import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output logs in structured JSON format.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields passed in extra={}
        if hasattr(record, "__dict__"):
            for key, val in record.__dict__.items():
                if key not in ["args", "asctime", "created", "exc_info", "exc_text", 
                              "filename", "funcName", "levelname", "levelno", "lineno", 
                              "module", "msecs", "msg", "name", "pathname", "process", 
                              "processName", "relativeCreated", "stack_info", "thread", "threadName"]:
                    log_entry[key] = val
                    
        return json.dumps(log_entry)

def setup_logging() -> None:
    root_logger = logging.getLogger()
    
    # Clean up existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Silence third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("repomind")
