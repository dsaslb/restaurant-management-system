from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Schedule, Notification
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """메인 페이지"""
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """대시보드 페이지"""
    # 직원 현황
    employee_count = User.query.filter_by(is_active=True).count()
    
    # 오늘의 근무 일정
    today = datetime.now().date()
    today_schedules = Schedule.query.filter(
        Schedule.date == today,
        Schedule.is_approved == True
    ).all()
    
    # 실제 스케줄 데이터가 없는 경우를 위한 예시 데이터
    if not today_schedules:
        today_schedules = [
            {
                'user': {'name': '김철수'},
                'start_time': datetime.strptime('09:00', '%H:%M').time(),
                'end_time': datetime.strptime('18:00', '%H:%M').time()
            },
            {
                'user': {'name': '이영희'},
                'start_time': datetime.strptime('10:00', '%H:%M').time(),
                'end_time': datetime.strptime('19:00', '%H:%M').time()
            },
            {
                'user': {'name': '박지민'},
                'start_time': datetime.strptime('11:00', '%H:%M').time(),
                'end_time': datetime.strptime('20:00', '%H:%M').time()
            }
        ]
    
    today_schedule_count = len(today_schedules)
    
    # 알림
    notification_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    # 재고 부족 항목 수
    low_stock_count = 5
    
    # 최근 재고 변동
    recent_transactions = [
        {
            'ingredient': {'name': '돼지고기', 'unit': 'kg'},
            'quantity': 10,
            'created_at': datetime.now() - timedelta(hours=2)
        },
        {
            'ingredient': {'name': '쌀', 'unit': 'kg'},
            'quantity': -5,
            'created_at': datetime.now() - timedelta(hours=4)
        },
        {
            'ingredient': {'name': '소고기', 'unit': 'kg'},
            'quantity': 15,
            'created_at': datetime.now() - timedelta(hours=6)
        }
    ]
    
    return render_template('main/dashboard.html',
                         employee_count=employee_count,
                         today_schedule_count=today_schedule_count,
                         notification_count=notification_count,
                         low_stock_count=low_stock_count,
                         recent_transactions=recent_transactions,
                         today_schedules=today_schedules) 