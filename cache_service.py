import redis
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from functools import wraps
import pickle
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)
load_dotenv()

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=False
        )
        self.default_ttl = timedelta(hours=1)

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"캐시 조회 중 오류 발생: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """캐시에 데이터 저장"""
        try:
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(
                key,
                int(ttl.total_seconds()),
                pickle.dumps(value)
            )
        except Exception as e:
            logger.error(f"캐시 저장 중 오류 발생: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"캐시 삭제 중 오류 발생: {str(e)}")
            return False

    def clear(self, pattern: str = '*') -> int:
        """패턴에 맞는 캐시 삭제"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"캐시 정리 중 오류 발생: {str(e)}")
            return 0

    def get_user_cache(self, user_id: int) -> Dict:
        """사용자 관련 캐시 조회"""
        try:
            key = f'user:{user_id}'
            data = self.get(key)
            if data:
                return data
            return {}
        except Exception as e:
            logger.error(f"사용자 캐시 조회 중 오류 발생: {str(e)}")
            return {}

    def set_user_cache(self, user_id: int, data: Dict) -> bool:
        """사용자 관련 캐시 저장"""
        try:
            key = f'user:{user_id}'
            return self.set(key, data)
        except Exception as e:
            logger.error(f"사용자 캐시 저장 중 오류 발생: {str(e)}")
            return False

    def get_attendance_cache(self, user_id: int, date: str) -> Optional[Dict]:
        """출근 기록 캐시 조회"""
        try:
            key = f'attendance:{user_id}:{date}'
            return self.get(key)
        except Exception as e:
            logger.error(f"출근 기록 캐시 조회 중 오류 발생: {str(e)}")
            return None

    def set_attendance_cache(self, user_id: int, date: str, data: Dict) -> bool:
        """출근 기록 캐시 저장"""
        try:
            key = f'attendance:{user_id}:{date}'
            return self.set(key, data)
        except Exception as e:
            logger.error(f"출근 기록 캐시 저장 중 오류 발생: {str(e)}")
            return False

    def get_schedule_cache(self, user_id: int, date: str) -> Optional[Dict]:
        """스케줄 캐시 조회"""
        try:
            key = f'schedule:{user_id}:{date}'
            return self.get(key)
        except Exception as e:
            logger.error(f"스케줄 캐시 조회 중 오류 발생: {str(e)}")
            return None

    def set_schedule_cache(self, user_id: int, date: str, data: Dict) -> bool:
        """스케줄 캐시 저장"""
        try:
            key = f'schedule:{user_id}:{date}'
            return self.set(key, data)
        except Exception as e:
            logger.error(f"스케줄 캐시 저장 중 오류 발생: {str(e)}")
            return False

def cached(ttl: Optional[timedelta] = None):
    """캐싱 데코레이터"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_service = CacheService()
            
            # 캐시 키 생성
            key_parts = [f.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            key = ":".join(key_parts)
            
            # 캐시에서 데이터 조회
            cached_data = cache_service.get(key)
            if cached_data is not None:
                return cached_data
            
            # 함수 실행 및 결과 캐싱
            result = f(*args, **kwargs)
            cache_service.set(key, result, ttl)
            return result
        return wrapper
    return decorator 