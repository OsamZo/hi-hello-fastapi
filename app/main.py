import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.chatbot_category.router import router as category_router
from app.chatbot_data.router import router as data_router
from app.exception import (
    http_exception_handler,
    validation_exception_handler,
    custom_validation_exception_handler,
    conflict_exception_handler
)
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import HTTPException
import uvicorn

# 애플리케이션 생성
app = FastAPI()

# 환경 구분
ENV = os.getenv("production", "development")  # 기본값은 'development'

# CORS 설정
if ENV == "development":
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]  # 개발 환경 도메인
else:
    origins = os.getenv("ALLOWED_ORIGINS", "https://hi-hello.site").split(",")  # 배포 환경 도메인

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://hi-hello.site"],  # 허용할 출처
    allow_credentials=True,  # 인증 정보 허용 (쿠키 등)
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 글로벌 예외 핸들러 등록
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, custom_validation_exception_handler)
app.add_exception_handler(HTTPException, conflict_exception_handler)

# 라우터 등록
app.include_router(category_router)
app.include_router(data_router)

# 개발과 배포에 따른 서버 설정
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Elastic Beanstalk에서 제공하는 PORT 사용
    host = "localhost" if ENV == "development" else "0.0.0.0"  # 호스트 설정
    reload = True if ENV == "production" else False  # 개발 환경에서만 reload 활성화

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )