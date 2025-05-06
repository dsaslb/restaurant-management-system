import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from functools import wraps
from flask import request, jsonify
import redis
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class SecurityManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=False
        )
        self.jwt_secret = os.getenv('JWT_SECRET', secrets.token_hex(32))
        self.api_key_expiry = timedelta(days=30)

    def generate_api_key(self, user_id: int) -> str:
        """API 키 생성"""
        try:
            api_key = secrets.token_hex(32)
            expiry = datetime.utcnow() + self.api_key_expiry
            
            # Redis에 API 키 저장
            self.redis_client.hset(
                f'api_keys:{user_id}',
                api_key,
                expiry.isoformat()
            )
            
            logger.info(f"API 키 생성: user_id={user_id}")
            return api_key
        except Exception as e:
            logger.error(f"API 키 생성 중 오류 발생: {str(e)}")
            raise

    def validate_api_key(self, api_key: str) -> Optional[int]:
        """API 키 검증"""
        try:
            # 모든 API 키 검색
            for key in self.redis_client.keys('api_keys:*'):
                user_id = key.decode().split(':')[1]
                if self.redis_client.hexists(key, api_key):
                    expiry = datetime.fromisoformat(
                        self.redis_client.hget(key, api_key).decode()
                    )
                    if datetime.utcnow() < expiry:
                        return int(user_id)
                    else:
                        # 만료된 키 삭제
                        self.redis_client.hdel(key, api_key)
            return None
        except Exception as e:
            logger.error(f"API 키 검증 중 오류 발생: {str(e)}")
            return None

    def revoke_api_key(self, user_id: int, api_key: str) -> bool:
        """API 키 취소"""
        try:
            return bool(
                self.redis_client.hdel(f'api_keys:{user_id}', api_key)
            )
        except Exception as e:
            logger.error(f"API 키 취소 중 오류 발생: {str(e)}")
            return False

    def list_api_keys(self, user_id: int) -> Dict[str, str]:
        """사용자의 API 키 목록 조회"""
        try:
            keys = self.redis_client.hgetall(f'api_keys:{user_id}')
            return {
                key.decode(): expiry.decode()
                for key, expiry in keys.items()
            }
        except Exception as e:
            logger.error(f"API 키 목록 조회 중 오류 발생: {str(e)}")
            return {}

    def create_jwt_token(self, user_id: int) -> str:
        """JWT 토큰 생성"""
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(hours=1),
                'iat': datetime.utcnow(),
                'iss': 'restaurant_system'
            }
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token
        except Exception as e:
            logger.error(f"JWT 토큰 생성 중 오류 발생: {str(e)}")
            raise

    def verify_jwt_token(self, token: str) -> Optional[int]:
        """JWT 토큰 검증"""
        try:
            if not token:
                return None
            
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256'],
                options={
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_iss': True,
                    'require': ['exp', 'iat', 'iss']
                }
            )
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            logger.warning("만료된 JWT 토큰")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"유효하지 않은 JWT 토큰: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"JWT 토큰 검증 중 오류 발생: {str(e)}")
            return None

def api_key_required(f):
    """API 키 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API 키가 필요합니다.'}), 401
            
        security_manager = SecurityManager()
        user_id = security_manager.validate_api_key(api_key)
        if not user_id:
            return jsonify({'error': '유효하지 않은 API 키입니다.'}), 401
            
        return f(user_id, *args, **kwargs)
    return decorated

def jwt_required(f):
    """JWT 토큰 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '토큰이 필요합니다.'}), 401
            
        token = token.replace('Bearer ', '')
        security_manager = SecurityManager()
        user_id = security_manager.verify_jwt_token(token)
        if not user_id:
            return jsonify({'error': '유효하지 않은 토큰입니다.'}), 401
            
        return f(user_id, *args, **kwargs)
    return decorated 