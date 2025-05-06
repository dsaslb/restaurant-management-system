from flask import Blueprint, request, jsonify, render_template, session
from models import Schedule, Employee, db, User, ScheduleHistory
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from utils.error_handler import ValidationError, DatabaseError, NotFoundError
from utils.response import api_response
from utils.decorators import db_session_required, validate_input, log_request
import logging
from utils.kakao_notify import send_kakao_notification

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')
logger = logging.getLogger(__name__)

@schedule_bp.route('/')
def index():
    return render_template('schedule.html')

@schedule_bp.route('/schedule')
@login_required
def schedule_page():
    """스케줄 관리 페이지"""
    if not current_user.is_admin:
        return render_template('error.html', message='접근 권한이 없습니다.'), 403
    return render_template('schedule/calendar.html')

@schedule_bp.route('/my_schedule')
@login_required
def my_schedule():
    """직원 스케줄 페이지"""
    try:
        # 현재 사용자의 스케줄 조회
        schedules = Schedule.query.filter_by(user_id=current_user.id).all()
        
        # 스케줄 데이터 변환
        schedule_list = [{
            'id': s.id,
            'date': s.date.strftime('%Y-%m-%d'),
            'start_time': s.start_time.strftime('%H:%M'),
            'end_time': s.end_time.strftime('%H:%M'),
            'confirmed': s.confirmed
        } for s in schedules]
        
        return render_template('schedule/my_schedule.html', schedules=schedule_list)
        
    except Exception as e:
        logger.error(f"직원 스케줄 조회 중 오류 발생: {str(e)}")
        return render_template('error.html', message='스케줄 조회 중 오류가 발생했습니다.'), 500

@schedule_bp.route('/api/schedule', methods=['GET'])
@jwt_required()
def get_schedule_events():
    """스케줄 이벤트 목록 조회"""
    try:
        # 현재 사용자 확인
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return api_response(
                status='error',
                message='로그인이 필요합니다.',
                status_code=401
            )
            
        # 스케줄 조회 (관리자는 전체, 직원은 자신의 스케줄만)
        if user.is_admin:
            schedules = Schedule.query.all()
        else:
            schedules = Schedule.query.filter_by(user_id=current_user_id).all()
            
        # 이벤트 데이터 변환
        events = []
        for schedule in schedules:
            employee = Employee.query.filter_by(user_id=schedule.user_id).first()
            if not employee:
                continue
            
            events.append({
                'id': schedule.id,
                'title': employee.user.name,
                'start': f'{schedule.date}T{schedule.start_time}',
                'end': f'{schedule.date}T{schedule.end_time}',
                'confirmed': schedule.confirmed,
                'backgroundColor': '#28a745' if schedule.confirmed else '#ffc107',
                'textColor': '#ffffff',
                'extendedProps': {
                    'employee_id': schedule.user_id,
                    'position': employee.position
                }
            })

        return api_response(
            status='success',
            data={'events': events}
        )
        
    except Exception as e:
        logger.error(f"스케줄 이벤트 조회 중 오류 발생: {str(e)}")
        return api_response(
            status='error',
            message=f'스케줄 이벤트 조회 중 오류가 발생했습니다: {str(e)}',
            status_code=500
        )

@schedule_bp.route('/api/employees', methods=['GET'])
@jwt_required()
def get_employees():
    """직원 목록 조회"""
    try:
        # 현재 사용자 확인
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return api_response(
                status='error',
                message='로그인이 필요합니다.',
                status_code=401
            )
            
        # 직원 목록 조회 (관리자만 전체 직원 조회 가능)
        if user.is_admin:
            employees = Employee.query.all()
        else:
            employees = Employee.query.filter_by(user_id=current_user_id).all()
            
        # 직원 데이터 변환
        employee_list = [{
            'id': emp.user_id,
            'name': emp.user.name,
            'position': emp.position
        } for emp in employees]
        
        return api_response(
            status='success',
            data={'employees': employee_list}
        )
        
    except Exception as e:
        logger.error(f"직원 목록 조회 중 오류 발생: {str(e)}")
        return api_response(
            status='error',
            message=f'직원 목록 조회 중 오류가 발생했습니다: {str(e)}',
            status_code=500
        )

@schedule_bp.route('/api/schedule', methods=['POST'])
@jwt_required()
@validate_input(required_fields=['user_id', 'start_time', 'end_time'])
@db_session_required
def save_schedule():
    """스케줄 저장"""
    try:
        # 현재 사용자 확인
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 관리자 권한 확인
        if not user or not user.is_admin:
            return api_response(
                status='error',
                message='권한이 없습니다.',
                status_code=403
            )
            
        # 요청 데이터 검증
        data = request.get_json()
        
        # 시간 형식 검증
        try:
            start_time = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S')
            end_time = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return api_response(
                status='error',
                message='날짜 또는 시간 형식이 올바르지 않습니다.',
                status_code=400
            )
            
        # 시간 유효성 검사
        if end_time <= start_time:
            return api_response(
                status='error',
                message='종료 시간은 시작 시간보다 이후여야 합니다.',
                status_code=400
            )
            
        # 직원 존재 확인
        employee = Employee.query.filter_by(user_id=data['user_id']).first()
        if not employee:
            return api_response(
                status='error',
                message='직원을 찾을 수 없습니다.',
                status_code=404
            )
            
        # 스케줄 중복 확인
        existing_schedule = Schedule.query.filter_by(
            user_id=data['user_id'],
            date=start_time.date()
        ).first()
        
        if existing_schedule:
            return api_response(
                status='error',
                message='해당 날짜에 이미 스케줄이 존재합니다.',
                status_code=400
            )
            
        # 새 스케줄 생성
        new_schedule = Schedule(
            user_id=data['user_id'],
            date=start_time.date(),
            start_time=start_time.time(),
            end_time=end_time.time(),
            confirmed=False,
            created_by=current_user_id
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        logger.info(f"새 스케줄 생성 완료: id={new_schedule.id}")
        
        return api_response(
            status='success',
            message='스케줄이 성공적으로 저장되었습니다.',
            data={'schedule_id': new_schedule.id}
        )
        
    except Exception as e:
        logger.error(f"스케줄 저장 중 오류 발생: {str(e)}")
        return api_response(
            status='error',
            message=f'스케줄 저장 중 오류가 발생했습니다: {str(e)}',
            status_code=500
        )

@schedule_bp.route('/api/schedule/<int:schedule_id>', methods=['PUT'])
@jwt_required()
@validate_input(required_fields=['start_time', 'end_time', 'reason'])
@db_session_required
def update_schedule(schedule_id):
    """스케줄 수정"""
    try:
        # 현재 사용자 확인
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 관리자 권한 확인
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': '권한이 없습니다.'
            }), 403
            
        # 스케줄 조회
        schedule = Schedule.query.get_or_404(schedule_id)
        
        # 요청 데이터 검증
        data = request.get_json()
        
        # 시간 유효성 검사
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        if end_time <= start_time:
            return jsonify({
                'status': 'error',
                'message': '종료 시간은 시작 시간보다 이후여야 합니다.'
            }), 400
            
        # 변경 이력 기록
        history = ScheduleHistory(
            schedule_id=schedule.id,
            changed_by=current_user_id,
            old_start=schedule.start_time.strftime('%H:%M'),
            old_end=schedule.end_time.strftime('%H:%M'),
            new_start=data['start_time'],
            new_end=data['end_time'],
            reason=data.get('reason', '')
        )
        
        # 스케줄 수정
        schedule.start_time = start_time
        schedule.end_time = end_time
        schedule.updated_at = datetime.utcnow()
        
        db.session.add(history)
        db.session.commit()
        
        logger.info(f"스케줄 수정 완료: id={schedule.id}, 변경자={current_user_id}")
        
        return jsonify({
            'status': 'success',
            'message': '스케줄이 성공적으로 수정되었습니다.'
        })
    except Exception as e:
        logger.error(f"스케줄 수정 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'스케줄 수정 중 오류가 발생했습니다: {str(e)}'
        }), 500

@schedule_bp.route('/api/schedule/<int:schedule_id>/history', methods=['GET'])
@jwt_required()
def get_schedule_history(schedule_id):
    """스케줄 변경 이력 조회"""
    try:
        # 현재 사용자 확인
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # 스케줄 조회
        schedule = Schedule.query.get_or_404(schedule_id)
        
        # 권한 확인 (관리자 또는 해당 스케줄의 직원)
        if not user.is_admin and schedule.user_id != current_user_id:
            return jsonify({
                'status': 'error',
                'message': '권한이 없습니다.'
            }), 403
            
        # 변경 이력 조회
        history = ScheduleHistory.query.filter_by(schedule_id=schedule_id)\
            .order_by(ScheduleHistory.changed_at.desc())\
            .all()
            
        # 이력 데이터 변환
        history_list = [{
            'id': h.id,
            'changed_at': h.changed_at.strftime('%Y-%m-%d %H:%M'),
            'changed_by': h.user.name,
            'old_start': h.old_start,
            'old_end': h.old_end,
            'new_start': h.new_start,
            'new_end': h.new_end,
            'reason': h.reason
        } for h in history]
        
        return jsonify({
            'status': 'success',
            'history': history_list
        })
        
    except Exception as e:
        logger.error(f"스케줄 이력 조회 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'스케줄 이력 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@schedule_bp.route('/api/schedule/<int:schedule_id>/confirm', methods=['POST'])
@login_required
@db_session_required
def confirm_schedule(schedule_id):
    """스케줄 확인"""
    try:
        # 스케줄 조회
        schedule = Schedule.query.get_or_404(schedule_id)
        
        # 권한 확인 (해당 스케줄의 직원만 확인 가능)
        if schedule.user_id != current_user.id:
            return api_response(
                status='error',
                message='권한이 없습니다.',
                status_code=403
            )
            
        # 이미 확인된 스케줄인지 확인
        if schedule.confirmed:
            return api_response(
                status='error',
                message='이미 확인된 스케줄입니다.',
                status_code=400
            )
            
        # 스케줄 확인 상태 업데이트
        schedule.confirmed = True
        schedule.confirmed_at = datetime.utcnow()
        schedule.confirmed_by = current_user.id
        
        db.session.commit()
        
        logger.info(f"스케줄 확인 완료: id={schedule.id}, user_id={current_user.id}")
        
        return api_response(
            status='success',
            message='스케줄이 확인되었습니다.'
        )
        
    except Exception as e:
        logger.error(f"스케줄 확인 중 오류 발생: {str(e)}")
        return api_response(
            status='error',
            message=f'스케줄 확인 중 오류가 발생했습니다: {str(e)}',
            status_code=500
        )

@schedule_bp.route('/api/schedule/employee/<int:employee_id>', methods=['GET'])
@jwt_required()
def get_employee_schedule(employee_id):
    schedules = Schedule.query.filter_by(employee_id=employee_id).all()
    return jsonify([{
        'id': s.id,
        'date': s.date.isoformat(),
        'start_time': s.start_time.strftime('%H:%M'),
        'end_time': s.end_time.strftime('%H:%M'),
        'confirmed': s.confirmed
    } for s in schedules]) 

@schedule_bp.route('/api/events', methods=['GET'])
def get_events():
    events = Schedule.query.all()
    data = [{
        "id": ev.id,
        "title": ev.title,
        "start": ev.start_time.isoformat(),
        "end": ev.end_time.isoformat()
    } for ev in events]
    return jsonify(data)

@schedule_bp.route('/api/events', methods=['POST'])
def create_event():
    payload = request.get_json()
    ev = Schedule(
        title=payload['title'],
        start_time=datetime.datetime.fromisoformat(payload['start']),
        end_time=datetime.datetime.fromisoformat(payload['end'])
    )
    db.session.add(ev)
    db.session.commit()
    return jsonify({"status": "success", "id": ev.id})

@schedule_bp.route('/api/events/<int:id>', methods=['PUT'])
def update_event(id):
    ev = Schedule.query.get_or_404(id)
    data = request.get_json()
    ev.actual_start = datetime.datetime.fromisoformat(data['actual_start'])
    ev.actual_end = datetime.datetime.fromisoformat(data['actual_end'])
    db.session.commit()

    # 스케줄 시작 시간과 실제 시작 시간 차이 (분)
    diff = abs((ev.actual_start - ev.start_time).total_seconds()) / 60
    if diff > 10:
        send_kakao_notification(
            admin_id=ev.admin_id,
            message=f"스케줄과 실제 근무시간 차이가 {int(diff)}분 발생했습니다."
        )
    return jsonify({"status": "updated"})
