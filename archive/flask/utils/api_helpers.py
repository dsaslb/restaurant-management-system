import os
import logging
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger('app')

def skip_if_no_key(func: Callable) -> Callable:
    """
    API 키가 없거나 비ASCII 문자인 경우 함수 실행을 건너뛰는 데코레이터
    
    Args:
        func: 데코레이트할 함수
        
    Returns:
        Callable: 데코레이트된 함수
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Optional[Any]:
        api_key = os.getenv('EXTERNAL_API_KEY')
        
        if not api_key:
            logger.warning('API 키가 설정되지 않아 동기화를 건너뜁니다.')
            return None
            
        try:
            api_key.encode('ascii')
        except UnicodeEncodeError:
            logger.warning('API 키에 비ASCII 문자가 포함되어 있어 동기화를 건너뜁니다.')
            return None
            
        return func(*args, **kwargs)
        
    return wrapper

def validate_api_response(response: Any) -> bool:
    """
    API 응답의 유효성을 검사합니다.
    
    Args:
        response: API 응답 객체
        
    Returns:
        bool: 응답이 유효한 경우 True, 그렇지 않은 경우 False
    """
    if not response:
        logger.error('API 응답이 비어있습니다.')
        return False
        
    if not hasattr(response, 'status_code'):
        logger.error('API 응답에 status_code가 없습니다.')
        return False
        
    if response.status_code != 200:
        logger.error(f'API 응답 오류: {response.status_code} - {response.text}')
        return False
        
    return True 