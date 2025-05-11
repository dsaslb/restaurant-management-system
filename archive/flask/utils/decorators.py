from functools import wraps
import time
from typing import Callable, Any, List, Optional
from flask import request, jsonify, flash, redirect, url_for
from models import db
from utils.error_handler import ValidationError, DatabaseError
from utils.logger import logger
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging
from flask_login import current_user

logger = logging.getLogger(__name__)

def db_session_required(func: Callable) -> Callable:
    """데이터베이스 세션 관리 데코레이터"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            db.session.commit()
            execution_time = time.time() - start_time
            logger.info(f"DB 작업 완료: {func.__name__}, 실행 시간: {execution_time:.2f}초")
            return result
        except Exception as e:
            db.session.rollback()
            logger.error(f"DB 작업 실패: {func.__name__}, 오류: {str(e)}")
            raise DatabaseError(f"데이터베이스 작업 중 오류가 발생했습니다: {str(e)}")
    return wrapper

def validate_input(required_fields: Optional[List[str]] = None, json_only: bool = True) -> Callable:
    """입력값 검증 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if json_only and not request.is_json:
                raise ValidationError("JSON 형식의 요청만 허용됩니다.")
            
            data = request.get_json() or {}
            missing = [field for field in required_fields or [] if field not in data]
            if missing:
                raise ValidationError(f"필수 필드가 누락되었습니다: {', '.join(missing)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_request(func: Callable) -> Callable:
    """API 요청 로깅 데코레이터"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"API 요청: {request.method} {request.path}, "
                f"IP: {request.remote_addr}, "
                f"응답 시간: {execution_time:.2f}초"
            )
            return result
        except Exception as e:
            logger.error(
                f"API 오류: {request.method} {request.path}, "
                f"IP: {request.remote_addr}, "
                f"오류: {str(e)}"
            )
            raise
    return wrapper

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('관리자 권한이 필요합니다.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function 