from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import User, Attendance, UserContract
from utils.salary_calculator import calculate_salary
from utils.notification import send_salary_notification
from datetime import datetime, timedelta
from extensions import db

salary_bp = Blueprint('salary', __name__)

@salary_bp.route('/api/salary/calculate', methods=['POST'])
@login_required
def calculate_user_salary():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not all([user_id, start_date, end_date]):
            return jsonify({
                'status': 'error',
                'message': '필수 항목이 누락되었습니다.'
            }), 400

        # 관리자만 다른 사용자의 급여를 조회할 수 있음
        if current_user.role != 'admin' and current_user.id != user_id:
            return jsonify({
                'status': 'error',
                'message': '권한이 없습니다.'
            }), 403

        # 급여 계산
        salary_info = calculate_salary(user_id, start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'data': salary_info
        })

    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'급여 계산 중 오류가 발생했습니다: {str(e)}'
        }), 500

@salary_bp.route('/api/salary/monthly/<int:user_id>', methods=['GET'])
@login_required
def get_monthly_salary(user_id):
    try:
        # 관리자만 다른 사용자의 급여를 조회할 수 있음
        if current_user.role != 'admin' and current_user.id != user_id:
            return jsonify({'status': 'error', 'message': '권한이 없습니다.'}), 403

        # 현재 월의 시작일과 종료일 계산
        today = datetime.now().date()
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        salary_info = calculate_salary(user_id, start_date, end_date)
        return jsonify({'status': 'success', 'data': salary_info})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@salary_bp.route('/api/salary/send-notification', methods=['POST'])
@login_required
def send_salary_notification_endpoint():
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '관리자만 알림을 보낼 수 있습니다.'}), 403

        data = request.get_json()
        user_id = data.get('user_id')
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

        if not all([user_id, start_date, end_date]):
            return jsonify({'status': 'error', 'message': '필수 항목이 누락되었습니다.'}), 400

        # 급여 계산
        salary_info = calculate_salary(user_id, start_date, end_date)
        
        # 알림 전송
        success = send_salary_notification(user_id, salary_info)
        
        if success:
            return jsonify({'status': 'success', 'message': '급여 알림이 전송되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': '알림 전송에 실패했습니다.'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@salary_bp.route('/api/salary/history/<int:user_id>', methods=['GET'])
@login_required
def get_salary_history(user_id):
    try:
        # 관리자만 다른 사용자의 급여 내역을 조회할 수 있음
        if current_user.role != 'admin' and current_user.id != user_id:
            return jsonify({'status': 'error', 'message': '권한이 없습니다.'}), 403

        # 최근 6개월 급여 내역 조회
        today = datetime.now().date()
        salary_history = []
        
        for i in range(6):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
                
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
                
            salary_info = calculate_salary(user_id, start_date, end_date)
            salary_history.append(salary_info)
            
        return jsonify({
            'status': 'success',
            'data': salary_history
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
