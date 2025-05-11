from models import db, Holiday
from datetime import datetime, date
import logging
from app import create_app

logger = logging.getLogger(__name__)

def init_holidays():
    """기본 공휴일 데이터 초기화"""
    app = create_app()
    with app.app_context():
        try:
            # 2024년 공휴일 목록
            holidays = [
                {'date': date(2024, 1, 1), 'name': '신정'},
                {'date': date(2024, 2, 9), 'name': '설날'},
                {'date': date(2024, 2, 10), 'name': '설날'},
                {'date': date(2024, 2, 12), 'name': '설날 대체공휴일'},
                {'date': date(2024, 3, 1), 'name': '삼일절'},
                {'date': date(2024, 5, 1), 'name': '근로자의 날'},
                {'date': date(2024, 5, 5), 'name': '어린이날'},
                {'date': date(2024, 5, 15), 'name': '석가탄신일'},
                {'date': date(2024, 6, 6), 'name': '현충일'},
                {'date': date(2024, 8, 15), 'name': '광복절'},
                {'date': date(2024, 9, 16), 'name': '추석'},
                {'date': date(2024, 9, 17), 'name': '추석'},
                {'date': date(2024, 9, 18), 'name': '추석 대체공휴일'},
                {'date': date(2024, 10, 3), 'name': '개천절'},
                {'date': date(2024, 10, 9), 'name': '한글날'},
                {'date': date(2024, 12, 25), 'name': '성탄절'}
            ]

            # 기존 데이터 삭제
            Holiday.query.delete()
            
            # 새 데이터 추가
            for holiday in holidays:
                db.session.add(Holiday(**holiday))
            
            db.session.commit()
            logger.info("공휴일 데이터 초기화 완료")
            
        except Exception as e:
            logger.error(f"공휴일 데이터 초기화 중 오류 발생: {str(e)}")
            db.session.rollback()
            raise 