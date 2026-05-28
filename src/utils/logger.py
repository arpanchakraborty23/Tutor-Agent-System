"""logger utility for highlighting important log messages.

This module provides a custom logger configuration that:
- Highlights important log levels (WARNING, ERROR, CRITICAL) with colors and emojis
- Uses structured JSON logging for production environments
- Provides console formatting with colors for development
- Supports log level filtering per module
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors and emojis to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    # Emojis for different log levels
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add emoji and color
        level_name = record.levelname
        color = self.COLORS.get(level_name, self.COLORS['RESET'])
        emoji = self.EMOJIS.get(level_name, '❓')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Build the log message
        log_msg = f"{color}[{timestamp}] {emoji} {level_name:8s} | {record.name} | {record.getMessage()}{self.COLORS['RESET']}"
        
        # Add exception info if present
        if record.exc_info:
            log_msg += f"\n{color}Exception: {self.formatException(record.exc_info)}{self.COLORS['RESET']}"
        
        return log_msg


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


class HighlightingLogger(logging.Logger):
    """Custom logger class with highlighting methods."""
    
    def important(self, msg: str, *args, **kwargs):
        """Log an important message with visual highlighting."""
        if self.isEnabledFor(logging.INFO):
            msg = f"✨ === {msg} === ✨"
            self._log(logging.INFO, msg, args, **kwargs)
    
    def success(self, msg: str, *args, **kwargs):
        """Log a success message with visual highlighting."""
        if self.isEnabledFor(logging.INFO):
            msg = f"✅ {msg}"
            self._log(logging.INFO, msg, args, **kwargs)
    
    def failure(self, msg: str, *args, **kwargs):
        """Log a failure message with visual highlighting."""
        if self.isEnabledFor(logging.ERROR):
            msg = f"❌ {msg}"
            self._log(logging.ERROR, msg, args, **kwargs)
    
    def highlight(self, msg: str, *args, **kwargs):
        """Log a highlighted message."""
        if self.isEnabledFor(logging.INFO):
            msg = f"🔔 >>> {msg} <<<<"
            self._log(logging.INFO, msg, args, **kwargs)
    
    def section(self, title: str, *args, **kwargs):
        """Log a section divider with title."""
        if self.isEnabledFor(logging.INFO):
            divider = "=" * 60
            msg = f"\n{divider}\n  📌 {title}\n{divider}"
            self._log(logging.INFO, msg, args, **kwargs)
    
    def data(self, label: str, data: Any, *args, **kwargs):
        """Log data with label and formatting."""
        if self.isEnabledFor(logging.DEBUG):
            formatted_data = json.dumps(data, indent=2, default=str) if isinstance(data, (dict, list)) else str(data)
            msg = f"📊 {label}:\n{formatted_data}"
            self._log(logging.DEBUG, msg, args, **kwargs)


# Register the custom logger class
logging.setLoggerClass(HighlightingLogger)


def setup_test_logger(
    name: Optional[str] = None,
    level: int = logging.DEBUG,
    log_file: Optional[str] = None,
    use_json: bool = False,
    use_colors: bool = True,
    highlight_modules: Optional[list[str]] = None,
    overwrite_file: bool = True
) -> HighlightingLogger:
    """
    Setup a test logger with highlighting capabilities.
    
    Args:
        name: Logger name (default: root logger)
        level: Logging level (default: DEBUG)
        log_file: Optional file path to log to
        use_json: Whether to use JSON formatting for file output
        use_colors: Whether to use colors in console output
        highlight_modules: List of module names to highlight at INFO level
        overwrite_file: If True, overwrite the log file on each session (default: True)
    
    Returns:
        Configured HighlightingLogger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if use_colors:
        console_formatter = ColoredFormatter()
    else:
        console_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use mode='w' to overwrite the file each time the logger is initialized
        # This ensures fresh logs for each session (mode='a' would append)
        file_mode = 'w' if overwrite_file else 'a'
        file_handler = logging.FileHandler(log_file, mode=file_mode)
        file_handler.setLevel(level)
        
        if use_json:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Highlight specific modules
    if highlight_modules:
        for module_name in highlight_modules:
            module_logger = logging.getLogger(module_name)
            module_logger.setLevel(logging.DEBUG)
    
    return logger


def get_test_logger(name: str = "test") -> HighlightingLogger:
    """Get a test logger with default configuration."""
    logger = logging.getLogger(name)
    
    # If logger already has handlers, return it
    if logger.handlers:
        return logger  # type: ignore
    
    # Setup with defaults
    return setup_test_logger(
        name=name,
        level=logging.DEBUG,
        use_colors=True,
    )


# Example usage and testing
if __name__ == "__main__":
    # Create test logger
    logger = setup_test_logger(
        name="test_logger",
        level=logging.DEBUG,
        log_file="logs/test.log",
        highlight_modules=["src.agents", "src.utils"]
    )
    
    # Test all log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test custom methods
    print()
    logger.section("Starting Test Suite")
    logger.important("This is an important message")
    logger.success("Operation completed successfully!")
    logger.failure("Operation failed!")
    logger.highlight("This is a highlighted message")
    logger.data("User Data", {"name": "John", "age": 30, "active": True})
    
    # Test exception logging
    print()
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("An error occurred")
