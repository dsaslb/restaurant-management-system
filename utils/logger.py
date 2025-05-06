import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(
    name: str,
    log_file: str = 'logs/server.log',
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    로거를 설정하고 반환합니다.
    
    Args:
        name: 로거 이름
        log_file: 로그 파일 경로
        level: 로깅 레벨
        max_bytes: 최대 파일 크기
        backup_count: 백업 파일 수
        
    Returns:
        logging.Logger: 설정된 로거
    """
    # 로그 디렉토리 생성
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 파일 핸들러 설정
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 전역 로거 인스턴스
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