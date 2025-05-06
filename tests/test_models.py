import unittest
from datetime import datetime, date, timedelta
from models import db, User, Store, Attendance, UserContract, Schedule, WorkLog, WorkFeedback
from app import app

class TestModels(unittest.TestCase):
    def setUp(self):
        """테스트 전 설정"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            
            # 테스트용 매장 생성
            self.store = Store(
                name='테스트 매장',
                address='서울시 강남구',
                phone='02-1234-5678'
            )
            db.session.add(self.store)
            db.session.commit()
            
            # 테스트용 사용자 생성
            self.user = User(
                username='testuser',
                password='testpass',
                name='테스트 사용자',
                role='employee',
                store_id=self.store.id,
                phone='010-1234-5678'
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """테스트 후 정리"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation(self):
        """사용자 생성 테스트"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'employee')
        self.assertEqual(self.user.store_id, self.store.id)

    def test_attendance_recording(self):
        """출근 기록 테스트"""
        attendance = Attendance(
            user_id=self.user.id,
            timestamp=datetime.now(),
            clock_in=datetime.now().time()
        )
        db.session.add(attendance)
        db.session.commit()
        
        self.assertEqual(attendance.user_id, self.user.id)
        self.assertIsNotNone(attendance.clock_in)

    def test_contract_creation(self):
        """계약 생성 테스트"""
        contract = UserContract(
            user_id=self.user.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            pay_type='시급',
            wage=9860
        )
        db.session.add(contract)
        db.session.commit()
        
        self.assertEqual(contract.user_id, self.user.id)
        self.assertEqual(contract.pay_type, '시급')

    def test_schedule_creation(self):
        """스케줄 생성 테스트"""
        schedule = Schedule(
            user_id=self.user.id,
            store_id=self.store.id,
            date=date.today(),
            planned_start=datetime.now().time(),
            planned_end=(datetime.now() + timedelta(hours=8)).time()
        )
        db.session.add(schedule)
        db.session.commit()
        
        self.assertEqual(schedule.user_id, self.user.id)
        self.assertEqual(schedule.store_id, self.store.id)

    def test_worklog_creation(self):
        """근무 기록 생성 테스트"""
        worklog = WorkLog(
            user_id=self.user.id,
            content='테스트 근무 기록',
            date=date.today()
        )
        db.session.add(worklog)
        db.session.commit()
        
        self.assertEqual(worklog.user_id, self.user.id)
        self.assertEqual(worklog.content, '테스트 근무 기록')

    def test_feedback_creation(self):
        """피드백 생성 테스트"""
        feedback = WorkFeedback(
            user_id=self.user.id,
            rating=5,
            comment='테스트 피드백',
            date=date.today()
        )
        db.session.add(feedback)
        db.session.commit()
        
        self.assertEqual(feedback.user_id, self.user.id)
        self.assertEqual(feedback.rating, 5)

if __name__ == '__main__':
    unittest.main() 