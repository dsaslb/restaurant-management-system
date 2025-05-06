from flask import current_app
from models import db, Ingredient, Notification, NotificationLog, User
from datetime import datetime

def notify_low_stock():
    """재고 부족 알림 전송"""
    try:
        # 재고 부족 품목 조회
        low_stock_items = Ingredient.query.filter(
            Ingredient.current_stock <= Ingredient.min_stock
        ).all()

        if not low_stock_items:
            return

        # 관리자에게 알림 전송
        admin_users = db.session.query(User).filter_by(is_admin=True).all()
        
        for admin in admin_users:
            # 알림 생성
            notification = Notification(
                recipient_id=admin.id,
                title="재고 부족 알림",
                content=f"다음 품목의 재고가 부족합니다:\n" + 
                       "\n".join([f"- {item.name}: {item.current_stock}{item.unit} (최소 {item.min_stock}{item.unit})" 
                                for item in low_stock_items]),
                notification_type="system"
            )
            db.session.add(notification)

            # 알림 로그 기록
            log = NotificationLog(
                notification_type="low_stock",
                content=f"재고 부족 알림 전송: {len(low_stock_items)}개 품목",
                recipient_id=admin.id,
                status="sent"
            )
            db.session.add(log)

        db.session.commit()

    except Exception as e:
        current_app.logger.error(f"재고 부족 알림 전송 중 오류 발생: {str(e)}")
        db.session.rollback() 