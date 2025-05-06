from datetime import date, timedelta, datetime
from models import User, UserContract, AlertLog, db
from flask import current_app
import logging
from functools import lru_cache
import jwt
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# JWT 설정
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(hours=1)

def create_jwt_token(user_id: int) -> str:
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@lru_cache(maxsize=100)
def get_user_alerts(user_id: int) -> List[Dict]:
    """사용자 알림 조회 (캐싱 적용)"""
    try:
        alerts = AlertLog.query.filter_by(user_id=user_id).order_by(AlertLog.created_at.desc()).all()
        return [{
            'id': alert.id,
            'type': alert.alert_type,
            'message': alert.message,
            'created_at': alert.created_at.isoformat()
        } for alert in alerts]
    except Exception as e:
        logger.error(f"사용자 알림 조회 중 오류 발생: {str(e)}")
        return []

def check_alerts() -> int:
    """알림 체크 및 발송 서비스"""
    try:
        today = date.today()
        one_month = timedelta(days=30)
        alerts_sent = 0

        # 배치 처리로 사용자 조회 최적화
        users = User.query.all()
        for user in users:
            try:
                # 보건증 갱신일 확인
                if user.health_certificate_expire and (user.health_certificate_expire - today).days <= 30:
                    message = f"[보건증] {user.name}님의 보건증이 곧 만료됩니다!"
                    if not AlertLog.query.filter_by(user_id=user.id, alert_type='보건증').first():
                        alert = AlertLog(user_id=user.id, alert_type='보건증', message=message)
                        db.session.add(alert)
                        if send_kakao_alert(user.phone, message):
                            alerts_sent += 1

                # 계약 만료 확인
                contract = UserContract.query.filter_by(user_id=user.id).order_by(UserContract.end_date.desc()).first()
                if contract and (contract.end_date - today).days <= 30:
                    message = f"[계약] {user.name}님의 계약이 {contract.end_date}에 종료됩니다."
                    if not AlertLog.query.filter_by(user_id=user.id, alert_type='계약').first():
                        alert = AlertLog(user_id=user.id, alert_type='계약', message=message)
                        db.session.add(alert)
                        if send_kakao_alert(user.phone, message):
                            alerts_sent += 1
            except Exception as e:
                logger.error(f"사용자 {user.id} 알림 처리 중 오류 발생: {str(e)}")
                continue

        db.session.commit()
        logger.info(f"알림 체크 완료: {alerts_sent}개의 알림이 발송되었습니다.")
        return alerts_sent

    except Exception as e:
        logger.error(f"알림 체크 중 오류 발생: {str(e)}")
        db.session.rollback()
        return 0

def send_kakao_alert(phone: str, message: str) -> bool:
    """카카오톡 알림 발송"""
    try:
        # 실제 API 연동 시에는 REST API로 전송
        logger.info(f"[카카오톡 발송] {phone} → {message}")
        return True
    except Exception as e:
        logger.error(f"카카오톡 발송 중 오류 발생: {str(e)}")
        return False

def get_alert_stats() -> Dict:
    """알림 통계 조회"""
    try:
        today = date.today()
        stats = {
            'total_alerts': AlertLog.query.count(),
            'today_alerts': AlertLog.query.filter(
                db.func.date(AlertLog.created_at) == today
            ).count(),
            'alert_types': db.session.query(
                AlertLog.alert_type,
                db.func.count(AlertLog.id)
            ).group_by(AlertLog.alert_type).all()
        }
        return stats
    except Exception as e:
        logger.error(f"알림 통계 조회 중 오류 발생: {str(e)}")
        return {}
