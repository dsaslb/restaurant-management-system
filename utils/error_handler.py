from flask import jsonify, request
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """API 에러의 기본 클래스"""
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        payload: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self) -> Dict[str, Any]:
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv

class ValidationError(Exception):
    """입력 데이터 검증 오류"""
    pass

class DatabaseError(Exception):
    """데이터베이스 작업 오류"""
    pass

class NotFoundError(Exception):
    """리소스를 찾을 수 없음"""
    pass

class AuthenticationError(APIError):
    """인증 실패"""
    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, payload)

class AuthorizationError(APIError):
    """권한 없음"""
    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message, 403, payload)

def register_error_handlers(app):
    """에러 핸들러 등록"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """API 에러 처리"""
        logger.error(f"API Error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        logger.warning(f"입력 데이터 검증 오류: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400
        
    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        logger.error(f"데이터베이스 오류: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': '데이터베이스 작업 중 오류가 발생했습니다.'
        }), 500
        
    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        logger.warning(f"리소스를 찾을 수 없음: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 404
        
    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({
            'status': 'error',
            'message': '요청한 리소스를 찾을 수 없습니다.'
        }), 404
        
    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f"서버 오류: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': '서버 오류가 발생했습니다.'
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """예상치 못한 에러 처리"""
        logger.error(f"Unexpected Error: {str(error)}")
        response = jsonify({
            'status': 'error',
            'message': '예상치 못한 오류가 발생했습니다.'
        })
        response.status_code = 500
        return response

    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error: AuthenticationError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error: AuthorizationError):
        return jsonify(error.to_dict()), error.status_code 