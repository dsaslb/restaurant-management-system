from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from contract_checker import check_contract_expiration
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """스케줄러 실행"""
    try:
        # 스케줄러 생성
        scheduler = BlockingScheduler()
        
        # 매일 오전 9시에 계약 만료 체크 실행
        scheduler.add_job(
            check_contract_expiration,
            CronTrigger(hour=9, minute=0),
            id='contract_check',
            name='계약 만료 체크',
            replace_existing=True
        )
        
        logger.info("스케줄러가 시작되었습니다.")
        scheduler.start()
        
    except Exception as e:
        logger.error(f"스케줄러 실행 중 오류 발생: {str(e)}")
        raise

if __name__ == '__main__':
    main() 