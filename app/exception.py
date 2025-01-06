from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail.get("error", "HTTPException"),
            "message": exc.detail.get("message", "An error occurred."),
            "debug_info": exc.detail.get("debug_info", None)
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Invalid request data.",
            "debug_info": exc.errors()
        }
    )

async def custom_validation_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.detail.get("error", "ValidationError"),
            "message": exc.detail.get("message", "Validation failed.")
        }
    )

async def conflict_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else exc.detail.get("error", "ConflictError"),
            "message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", "A conflict occurred."),
        },
    )