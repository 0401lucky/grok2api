"""
鍝嶅簲涓棿浠?
Response Middleware

鐢ㄤ簬璁板綍璇锋眰鏃ュ織銆佺敓鎴?TraceID 鍜岃绠楄姹傝€楁椂
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.logger import logger

class ResponseLoggerMiddleware(BaseHTTPMiddleware):
    """
    璇锋眰鏃ュ織/鍝嶅簲杩借釜涓棿浠?
    Request Logging and Response Tracking Middleware
    """
    
    async def dispatch(self, request: Request, call_next):
        # 鐢熸垚璇锋眰 ID
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        start_time = time.time()
        
        # 璁板綍璇锋眰淇℃伅
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "traceID": trace_id,
                "method": request.method,
                "path": request.url.path
            }
        )
        
        try:
            response = await call_next(request)
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("Referrer-Policy", "same-origin")
            response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
            response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data: https: blob:; media-src 'self' https: blob:; connect-src 'self' https: ws: wss:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            )
            
            # 璁＄畻鑰楁椂
            duration = (time.time() - start_time) * 1000
            
            # 璁板綍鍝嶅簲淇℃伅
            logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code} ({duration:.2f}ms)",
                extra={
                    "traceID": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(duration, 2)
                }
            )
            
            return response
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"Response Error: {request.method} {request.url.path} - {str(e)} ({duration:.2f}ms)",
                extra={
                    "traceID": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration, 2),
                    "error": str(e)
                }
            )
            raise e
