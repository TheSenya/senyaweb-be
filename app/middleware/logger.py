"""
Robust logging module for the application.
Provides a configured logger and a request/response logging middleware.
"""
import logging
import sys
import time
import uuid
from functools import wraps
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import ENV


# ============================================================================
# Logger Configuration
# ============================================================================

def setup_logger(name: str = "senyaweb") -> logging.Logger:
    """
    Set up and return a configured logger.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Set log level based on environment
    is_dev = ENV.lower() in ("dev", "local")
    logger.setLevel(logging.DEBUG if is_dev else logging.INFO)
    
    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if is_dev else logging.INFO)
    
    # Format: timestamp - level - name - message
    if is_dev:
        # More verbose format for development
        formatter = logging.Formatter(
            "\033[90m%(asctime)s\033[0m | "
            "%(levelname)-8s | "
            "\033[36m%(name)s\033[0m | "
            "%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Production format (no colors, more structured)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Create the main application logger
logger = setup_logger()


# ============================================================================
# Request/Response Logging Middleware
# ============================================================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every incoming request and outgoing response.
    
    Logs include:
    - Request: method, URL, headers (in dev), query params, client IP
    - Response: status code, response time, content length
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate a unique request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        
        # Start timing
        start_time = time.perf_counter()
        
        # Get request details
        method = request.method
        url = str(request.url)
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        
        # Log the incoming request
        is_dev = ENV.lower() in ("dev", "local")
        
        logger.info(f"[{request_id}] ➡️  {method} {path}")
        
        if is_dev:
            if query_params:
                logger.debug(f"[{request_id}]    Query: {query_params}")
            
            # Log headers in dev (excluding sensitive ones)
            headers_to_log = {
                k: v for k, v in request.headers.items()
                if k.lower() not in ("authorization", "cookie", "x-api-key")
            }
            if headers_to_log:
                logger.debug(f"[{request_id}]    Headers: {headers_to_log}")
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.perf_counter() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            # Get response details
            status_code = response.status_code
            content_length = response.headers.get("content-length", "unknown")
            
            # Choose emoji based on status code
            if status_code < 300:
                status_emoji = "✅"
            elif status_code < 400:
                status_emoji = "↪️"
            elif status_code < 500:
                status_emoji = "⚠️"
            else:
                status_emoji = "❌"
            
            logger.info(
                f"[{request_id}] {status_emoji} {status_code} | {process_time_ms}ms | {content_length} bytes"
            )
            
            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate response time even on error
            process_time = time.perf_counter() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            logger.error(f"[{request_id}] ❌ Exception: {type(e).__name__}: {str(e)}")
            logger.error(f"[{request_id}] ⏱️  Failed after {process_time_ms}ms")
            raise


# ============================================================================
# Function/Method Logging Decorator
# ============================================================================

def log_function(
    log_args: bool = True,
    log_result: bool = True,
    log_level: int = logging.DEBUG
) -> Callable:
    """
    Decorator to log function calls with arguments and return values.
    
    Args:
        log_args: Whether to log function arguments
        log_result: Whether to log the return value
        log_level: The logging level to use
        
    Usage:
        @log_function()
        def my_function(x, y):
            return x + y
            
        @log_function(log_args=True, log_result=True)
        async def my_async_function(data):
            return process(data)
    """
    def decorator(func: Callable) -> Callable:
        func_name = func.__qualname__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Log function entry
            if log_args:
                # Filter out 'self' from args display
                display_args = args[1:] if args and hasattr(args[0], '__class__') else args
                logger.log(log_level, f"📥 {func_name}(args={display_args}, kwargs={kwargs})")
            else:
                logger.log(log_level, f"📥 {func_name}()")
            
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                
                if log_result:
                    # Truncate long results
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    logger.log(log_level, f"📤 {func_name} -> {result_str} ({elapsed}ms)")
                else:
                    logger.log(log_level, f"📤 {func_name} completed ({elapsed}ms)")
                    
                return result
                
            except Exception as e:
                elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                logger.error(f"💥 {func_name} raised {type(e).__name__}: {str(e)} ({elapsed}ms)")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Log function entry
            if log_args:
                display_args = args[1:] if args and hasattr(args[0], '__class__') else args
                logger.log(log_level, f"📥 {func_name}(args={display_args}, kwargs={kwargs})")
            else:
                logger.log(log_level, f"📥 {func_name}()")
            
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                
                if log_result:
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    logger.log(log_level, f"📤 {func_name} -> {result_str} ({elapsed}ms)")
                else:
                    logger.log(log_level, f"📤 {func_name} completed ({elapsed}ms)")
                    
                return result
                
            except Exception as e:
                elapsed = round((time.perf_counter() - start_time) * 1000, 2)
                logger.error(f"💥 {func_name} raised {type(e).__name__}: {str(e)} ({elapsed}ms)")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator