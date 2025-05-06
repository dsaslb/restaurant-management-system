import requests
import os
from dotenv import load_dotenv
import logging
from models import Notification, User, db, AlertLog
from datetime import datetime
from config import Config

load_dotenv()

logger = logging.getLogger(__name__)

def send_admin_alert(message):
    """관리자에게 알림을 보냅니다."""
    logger.info(f"Admin alert: {message}")
    return True

def send_kakao_alert(phone_number, message):
    """카카오 알림톡을 보냅니다."""
    logger.info(f"Kakao alert to {phone_number}: {message}")
    return True

def send_alert(message, recipient_id=None, notification_type='system'):
    """일반 알림 전송"""
    try:
        notification = Notification(
            recipient_id=recipient_id,
            title="시스템 알림",
            content=message,
            notification_type=notification_type,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        logger.info(f"알림 전송 완료: {message}")
    except Exception as e:
        logger.error(f"알림 전송 실패: {str(e)}")
        db.session.rollback()


