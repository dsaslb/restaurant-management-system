import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from flask import has_request_context, request, current_app

class RequestFormatter(logging.Formatter):
    """요청 컨텍스트를 포함하는 로그 포맷터"""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            
        return super().format(record)

def setup_logger(name):
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 로그 디렉토리 생성
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 파일 핸들러 설정
    log_file = os.path.join(log_dir, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger

# 전역 로거 인스턴스 생성
logger = setup_logger('restaurant_system')

def log_request(logger: logging.Logger, request_data: dict, response_data: dict, duration: float):
    """API 요청 로깅"""
    logger.info(
        f"Request: {request_data.get('method')} {request_data.get('path')} - "
        f"Duration: {duration:.2f}s - "
        f"Status: {response_data.get('status_code')}"
    )

def log_error(logger: logging.Logger, error: Exception, context: Optional[dict] = None):
    """에러 로깅"""
    logger.error(
        f"Error: {str(error)} - "
        f"Context: {context if context else 'None'}"
    )

def log_database(logger: logging.Logger, operation: str, duration: float):
    """데이터베이스 작업 로깅"""
    logger.debug(
        f"Database {operation} - "
        f"Duration: {duration:.2f}s"
    ) 