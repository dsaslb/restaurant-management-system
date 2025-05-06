from datetime import date, timedelta, datetime
from models.employee import User
from models.notification import AlertLog
from models.inventory import InventoryItem, InventoryBatch
from extensions import db
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

def create_alert_log(
    alert_type: str,
    message: str,
    reference_id: int,
    user_id: Optional[int] = None
) -> AlertLog:
    """
    알림 로그 생성
    
    Args:
        alert_type (str): 알림 유형
        message (str): 알림 메시지
        reference_id (int): 참조 ID
        user_id (Optional[int]): 사용자 ID
    
    Returns:
        AlertLog: 생성된 알림 로그
    """
    alert = AlertLog(
        user_id=user_id or current_app.config['ADMIN_USER_ID'],
        alert_type=alert_type,
        message=message,
        reference_id=reference_id
    )
    db.session.add(alert)
    return alert

def check_expiring_batches(days_threshold: int = 3) -> List[AlertLog]:
    """
    유통기한 임박 배치 확인
    
    Args:
        days_threshold (int): 알림 기준일 (기본값: 3일)
    
    Returns:
        List[AlertLog]: 생성된 알림 로그 목록
    """
    today = date.today()
    threshold = today + timedelta(days=days_threshold)
    
    batches = (
        InventoryBatch.query
        .filter(
            InventoryBatch.expiration_date <= threshold,
            InventoryBatch.expiration_date >= today,
            (InventoryBatch.quantity - InventoryBatch.used_quantity) > 0
        )
        .all()
    )
    
    alerts = []
    for batch in batches:
        item_name = batch.item.name
        days_left = (batch.expiration_date - today).days
        message = f"[유통기한 경고] {item_name} 유통기한 {batch.expiration_date}까지 {days_left}일 남음"
        
        # 중복 발송 방지
        exists = AlertLog.query.filter_by(
            alert_type='expiration',
            reference_id=batch.id,
            created_at=date.today()
        ).first()
        
        if not exists:
            alert = create_alert_log('expiration', message, batch.id)
            alerts.append(alert)
            
            # 카카오 알림톡 전송
            if send_kakao_alert(current_app.config['ADMIN_PHONE'], message):
                logger.info(f"유통기한 알림 전송 성공: {message}")
            else:
                logger.warning(f"유통기한 알림 전송 실패: {message}")
    
    db.session.commit()
    return alerts

def check_low_stock() -> List[AlertLog]:
    """
    재고 부족 품목 확인
    
    Returns:
        List[AlertLog]: 생성된 알림 로그 목록
    """
    items = InventoryItem.query.all()
    alerts = []
    
    for item in items:
        if item.current_quantity <= item.min_quantity:
            message = f"[재고 부족] {item.name} 현재 재고: {item.current_quantity}{item.unit} (최소: {item.min_quantity}{item.unit})"
            
            # 중복 발송 방지
            exists = AlertLog.query.filter_by(
                alert_type='low_stock',
                reference_id=item.id,
                created_at=date.today()
            ).first()
            
            if not exists:
                alert = create_alert_log('low_stock', message, item.id)
                alerts.append(alert)
                
                # 카카오 알림톡 전송
                if send_kakao_alert(current_app.config['ADMIN_PHONE'], message):
                    logger.info(f"재고 부족 알림 전송 성공: {message}")
                else:
                    logger.warning(f"재고 부족 알림 전송 실패: {message}")
    
    db.session.commit()
    return alerts

def check_expired_batches() -> List[AlertLog]:
    """
    유통기한 만료 배치 확인
    
    Returns:
        List[AlertLog]: 생성된 알림 로그 목록
    """
    today = date.today()
    
    batches = (
        InventoryBatch.query
        .filter(
            InventoryBatch.expiration_date < today,
            (InventoryBatch.quantity - InventoryBatch.used_quantity) > 0
        )
        .all()
    )
    
    alerts = []
    for batch in batches:
        item_name = batch.item.name
        message = f"[유통기한 만료] {item_name} 유통기한 {batch.expiration_date} 만료"
        
        # 중복 발송 방지
        exists = AlertLog.query.filter_by(
            alert_type='expired',
            reference_id=batch.id,
            created_at=date.today()
        ).first()
        
        if not exists:
            alert = create_alert_log('expired', message, batch.id)
            alerts.append(alert)
            
            # 카카오 알림톡 전송
            if send_kakao_alert(current_app.config['ADMIN_PHONE'], message):
                logger.info(f"유통기한 만료 알림 전송 성공: {message}")
            else:
                logger.warning(f"유통기한 만료 알림 전송 실패: {message}")
    
    db.session.commit()
    return alerts

def run_all_checks() -> dict:
    """
    모든 알림 확인 실행
    
    Returns:
        dict: 각 알림 유형별 생성된 알림 수
    """
    expiring_alerts = check_expiring_batches()
    low_stock_alerts = check_low_stock()
    expired_alerts = check_expired_batches()
    
    return {
        'expiring': len(expiring_alerts),
        'low_stock': len(low_stock_alerts),
        'expired': len(expired_alerts)
    }
