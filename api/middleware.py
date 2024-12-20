# src/api/middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logger import logger
import time
import json
from typing import Callable

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        request_id = request.headers.get('X-Request-ID', str(time.time()))
        
        # Log request
        logger.info("Incoming request", {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "headers": dict(request.headers)
        })

        try:
            # Get request body
            body = await request.body()
            if body:
                try:
                    body_json = json.loads(body)
                    logger.info("Request body", {
                        "request_id": request_id,
                        "body": body_json
                    })
                except json.JSONDecodeError:
                    pass

            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info("Request completed", {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2)
            })
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error("Request failed", {
                "request_id": request_id,
                "error": str(e),
                "process_time_ms": round(process_time * 1000, 2)
            })
            raise