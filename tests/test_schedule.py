import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from models import Schedule, ScheduleHistory, User, Employee, db
from utils.alerts import send_alert
from scheduler.tasks import alert_unconfirmed_schedules
from app import create_app

@pytest.fixture
def app():
    """테스트용 Flask 애플리케이션 생성"""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """테스트용 클라이언트 생성"""
    return app.test_client()

@pytest.fixture
def test_user():
    """테스트용 관리자 사용자 생성"""
    user = User(
        username='testuser',
        name='테스트 사용자',
        is_admin=True
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_employee(test_user):
    """테스트용 직원 생성"""
    employee = Employee(
        user_id=test_user.id,
        position='테스트 직책'
    )
    db.session.add(employee)
    db.session.commit()
    return employee

@pytest.fixture
def test_schedule(test_employee):
    """테스트용 스케줄 생성"""
    schedule = Schedule(
        user_id=test_employee.user_id,
        date=datetime.now().date(),
        start_time=datetime.strptime('09:00', '%H:%M').time(),
        end_time=datetime.strptime('18:00', '%H:%M').time(),
        confirmed=False
    )
    db.session.add(schedule)
    db.session.commit()
    return schedule

def test_create_schedule(client, test_user, test_employee):
    """일정 생성 테스트"""
    # JWT 토큰 생성
    token = create_access_token(identity=test_user.id)
    
    # 일정 생성 요청
    response = client.post('/api/schedule',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'user_id': test_employee.user_id,
            'date': datetime.now().date().isoformat(),
            'start_time': '09:00',
            'end_time': '18:00'
        }
    )
    
    assert response.status_code == 200
    assert Schedule.query.count() == 1

def test_update_schedule(client, test_user, test_schedule):
    """일정 수정 테스트"""
    token = create_access_token(identity=test_user.id)
    
    # 일정 수정 요청
    response = client.put(f'/api/schedule/{test_schedule.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'start_time': '10:00',
            'end_time': '19:00',
            'reason': '테스트 수정'
        }
    )
    
    assert response.status_code == 200
    assert ScheduleHistory.query.count() == 1
    
    history = ScheduleHistory.query.first()
    assert history.old_start == '09:00'
    assert history.new_start == '10:00'
    assert history.reason == '테스트 수정'

def test_get_schedule_history(client, test_user, test_schedule):
    """이력 조회 테스트"""
    token = create_access_token(identity=test_user.id)
    
    # 이력 조회 요청
    response = client.get(f'/api/schedule/{test_schedule.id}/history',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'history' in data

def test_alert_unconfirmed_schedules(mocker, test_schedule):
    """미확인 스케줄 알림 테스트"""
    # 알림 전송 함수 모킹
    mock_send_alert = mocker.patch('utils.alerts.send_alert')
    
    # 테스트를 위해 스케줄 날짜를 어제로 설정
    test_schedule.date = datetime.now().date() - timedelta(days=1)
    db.session.commit()
    
    # 알림 함수 실행
    alert_unconfirmed_schedules()
    
    # 알림이 전송되었는지 확인
    mock_send_alert.assert_called_once()
    assert '확인하지 않았습니다' in mock_send_alert.call_args[0][0]

def test_schedule_permissions(client, test_user, test_schedule):
    """권한 테스트"""
    # 일반 사용자 토큰 생성
    regular_user = User(username='regular', name='일반 사용자', is_admin=False)
    db.session.add(regular_user)
    db.session.commit()
    
    token = create_access_token(identity=regular_user.id)
    
    # 일정 수정 시도
    response = client.put(f'/api/schedule/{test_schedule.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'start_time': '10:00',
            'end_time': '19:00',
            'reason': '테스트 수정'
        }
    )
    
    assert response.status_code == 403
    assert '권한이 없습니다' in response.get_json()['message'] 