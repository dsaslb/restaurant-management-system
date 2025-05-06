from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from flask import current_app
from models.inventory import InventoryBatch
from models.notification import Notification
from extensions import db
import logging
from utils.pos_service import sync_pos_sales
from utils.inventory import check_inventory_status
import pytz

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

def init_scheduler(app_scheduler):
    """스케줄러 초기화"""
    global scheduler
    scheduler = app_scheduler
    
    try:
        # POS 판매 데이터 동기화 (5분마다)
        scheduler.add_job(
            sync_pos_sales,
            trigger=IntervalTrigger(minutes=5, timezone=pytz.timezone('Asia/Seoul')),
            id='sync_pos_sales',
            name='POS 판매 데이터 동기화',
            replace_existing=True
        )
        
        # 재고 상태 확인 (매일 오전 9시)
        scheduler.add_job(
            check_inventory_status,
            trigger=CronTrigger(hour=9, timezone=pytz.timezone('Asia/Seoul')),
            id='check_inventory',
            name='재고 상태 확인',
            replace_existing=True
        )
        
        logger.info('스케줄러가 초기화되었습니다.')
    except Exception as e:
        logger.error(f'스케줄러 초기화 중 오류 발생: {str(e)}')
        raise

def get_scheduler_status():
    """스케줄러 상태 조회"""
    if scheduler is None:
        return {
            'status': 'not_initialized',
            'jobs': []
        }
    
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'status': 'running' if scheduler.running else 'stopped',
            'jobs': jobs
        }
    except Exception as e:
        logger.error(f'스케줄러 상태 조회 중 오류 발생: {str(e)}')
        return {
            'status': 'error',
            'error': str(e)
        }


