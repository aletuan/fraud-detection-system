import logging
import socket
import json
import time
from typing import Dict, Any
from datetime import datetime

class LogstashHandler(logging.Handler):
    """Custom logging handler that sends logs to Logstash via TCP"""
    
    def __init__(self, host: str, port: int):
        """Initialize the handler
        
        Args:
            host: Logstash host
            port: Logstash port
        """
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.hostname = socket.gethostname()
        
    def connect(self) -> bool:
        """Connect to Logstash server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.sock is None:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
            return True
        except Exception as e:
            self.sock = None
            return False
            
    def emit(self, record: logging.LogRecord):
        """Send log record to Logstash
        
        Args:
            record: Log record to send
        """
        try:
            # Format the message
            msg = self.format(record)
            
            # Create the log entry
            log_entry = {
                "@timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "service": "fraud-detection",
                "environment": "development",
                "log_type": "application",
                "level": record.levelname,
                "logger": record.name,
                "message": msg,
                "host": self.hostname
            }
            
            # Add extra fields if present
            if hasattr(record, "transaction_id"):
                log_entry["transaction_id"] = record.transaction_id
            if hasattr(record, "duration"):
                log_entry["duration"] = record.duration
            if hasattr(record, "method"):
                log_entry["method"] = record.method
            if hasattr(record, "path"):
                log_entry["path"] = record.path
            if hasattr(record, "status"):
                log_entry["status"] = record.status
                
            # Convert to JSON and add newline
            log_json = json.dumps(log_entry) + "\n"
            
            # Try to send, reconnecting if necessary
            if not self.sock and not self.connect():
                return
                
            try:
                self.sock.send(log_json.encode())
            except Exception:
                self.sock = None
                if self.connect():
                    self.sock.send(log_json.encode())
                    
        except Exception as e:
            self.handleError(record)

def setup_logging(
    logstash_host: str = "logstash",
    logstash_port: int = 5044,
    log_level: str = "INFO"
) -> None:
    """Setup logging configuration
    
    Args:
        logstash_host: Logstash host
        logstash_port: Logstash port
        log_level: Logging level
    """
    # Create logstash handler
    logstash_handler = LogstashHandler(logstash_host, logstash_port)
    logstash_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Set formatter for both handlers
    logstash_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Get root logger and set level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers and add new ones
    root_logger.handlers = []
    root_logger.addHandler(logstash_handler)
    root_logger.addHandler(console_handler) 