from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from flask import current_app
from models.inventory import InventoryBatch, InventoryItem
from models.notification import Notification
from extensions import db
import logging
from utils.pos_service import sync_pos_sales
from utils.inventory import check_inventory_status
import pytz
from models.order import Order

logger = logging.getLogger(__name__)

# 전역 스케줄러 인스턴스
scheduler = None

def check_expiring_items():
    """유통기한이 임박한 재고 확인"""
    try:
        with current_app.app_context():
            today = datetime.now().date()
            warning_threshold = today + timedelta(days=3)
            
            expiring_batches = (
                InventoryBatch.query
                .filter(InventoryBatch.expiration_date <= warning_threshold)
                .filter(InventoryBatch.expiration_date > today)
                .filter((InventoryBatch.quantity - InventoryBatch.used_quantity) > 0)
                .all()
            )
            
            for batch in expiring_batches:
                notification = Notification(
                    title="유통기한 임박 알림",
                    message=f"{batch.item.name}의 유통기한이 {batch.expiration_date}까지 남았습니다.",
                    type="warning"
                )
                db.session.add(notification)
            
            db.session.commit()
            logger.info(f"유통기한 임박 재고 확인 완료: {len(expiring_batches)}개 항목 발견")
    except Exception as e:
        logger.error(f"유통기한 임박 재고 확인 중 오류 발생: {str(e)}")
        db.session.rollback()

def init_scheduler():
    """스케줄러 초기화"""
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.start()
        logger.info('스케줄러가 시작되었습니다.')

def get_scheduler_status():
    """스케줄러 상태 확인"""
    global scheduler
    if scheduler is None:
        return '스케줄러가 초기화되지 않았습니다.'
    return '스케줄러가 실행 중입니다.' if scheduler.running else '스케줄러가 중지되었습니다.'

def check_inventory_levels():
    """재고 수준 확인"""
    try:
        items = InventoryItem.query.all()
        for item in items:
            if item.current_quantity <= item.minimum_quantity:
                notification = Notification(
                    title='재고 부족 알림',
                    message=f'{item.name}의 재고가 부족합니다. 현재 수량: {item.current_quantity}',
                    type='inventory_alert',
                    status='unread'
                )
                db.session.add(notification)
        db.session.commit()
        logger.info('재고 수준 확인이 완료되었습니다.')
    except Exception as e:
        logger.error(f'재고 수준 확인 중 오류 발생: {str(e)}')

def check_expiring_batches():
    """유통기한 임박 재고 확인"""
    try:
        today = datetime.utcnow().date()
        expiring_soon = today + timedelta(days=7)
        batches = InventoryBatch.query.filter(
            InventoryBatch.expiry_date <= expiring_soon,
            InventoryBatch.expiry_date >= today
        ).all()

        for batch in batches:
            notification = Notification(
                title='유통기한 임박 알림',
                message=f'{batch.item.name}의 유통기한이 {batch.expiry_date}에 만료됩니다.',
                type='expiry_alert',
                status='unread'
            )
            db.session.add(notification)
        db.session.commit()
        logger.info('유통기한 확인이 완료되었습니다.')
    except Exception as e:
        logger.error(f'유통기한 확인 중 오류 발생: {str(e)}')

def check_pending_orders():
    """미처리 주문 확인"""
    try:
        orders = Order.query.filter_by(status='pending').all()
        for order in orders:
            notification = Notification(
                title='미처리 주문 알림',
                message=f'주문 #{order.id}가 처리 대기 중입니다.',
                type='order_alert',
                status='unread'
            )
            db.session.add(notification)
        db.session.commit()
        logger.info('미처리 주문 확인이 완료되었습니다.')
    except Exception as e:
        logger.error(f'미처리 주문 확인 중 오류 발생: {str(e)}')

def schedule_tasks():
    """작업 스케줄링"""
    global scheduler
    if scheduler is None:
        init_scheduler()

    # 재고 수준 확인 - 매일 오전 9시
    scheduler.add_job(check_inventory_levels, 'cron', hour=9)

    # 유통기한 확인 - 매일 오전 10시
    scheduler.add_job(check_expiring_batches, 'cron', hour=10)

    # 미처리 주문 확인 - 매 시간마다
    scheduler.add_job(check_pending_orders, 'interval', hours=1)

    logger.info('모든 작업이 스케줄링되었습니다.')


