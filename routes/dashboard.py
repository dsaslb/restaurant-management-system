from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
import logging
from models import Contract, Schedule, Attendance, InventoryItem, WorkFeedback, User, Employee, SalesRecord, StockItem, Ingredient, MenuItem
from datetime import datetime, timedelta, date
from sqlalchemy import func, desc
from utils.salary_utils import calculate_salary
from utils.alerts import send_alert
from utils.gpt_analysis import analyze_feedback, analyze_contract_text, analyze_lateness, generate_store_report
from utils.decorators import admin_required

# 로깅 설정
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/admin')

@dashboard_bp.route('/dashboard')
@login_required
@admin_required
@dashboard_bp.route('/api/dashboard', methods=['GET'])
def admin_dashboard():
    """관리자 대시보드 데이터 조회"""
    try:
        today = datetime.utcnow().date()
        end_limit = today + timedelta(days=30)

        # 1. 계약 만료 임박
        expiring_contracts = Contract.query.filter(
            Contract.end_date <= end_limit,
            Contract.end_date > today
        ).all()

        # 2. 미확인 스케줄
        unconfirmed_schedules = Schedule.query.filter(
            Schedule.confirmed == False,
            Schedule.date >= today
        ).all()

        # 3. 재고 경고
        low_inventory = InventoryItem.query.filter(
            InventoryItem.quantity <= InventoryItem.min_quantity
        ).all()

        # 4. 피드백 요약
        feedbacks = WorkFeedback.query.order_by(
            WorkFeedback.submitted_at.desc()
        ).limit(5).all()

        # 5. 피드백 분석
        recent_feedbacks = WorkFeedback.query.order_by(
            WorkFeedback.submitted_at.desc()
        ).limit(10).all()
        feedback_analysis = analyze_feedback(recent_feedbacks)

        # 6. 월 급여 합계
        first_day = today.replace(day=1)
        last_day = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        total_salary = 0
        employees = User.query.filter_by(role='employee').all()
        
        for employee in employees:
            try:
                result = calculate_salary(employee.id, str(first_day), str(last_day))
                total_salary += result['calculated_salary']
            except Exception as e:
                send_alert(f"급여 계산 오류: {employee.name} ({str(e)})", notification_type='salary')
                continue

        return jsonify({
            'status': 'success',
            'data': {
                'expiring_contracts': [{
                    'id': c.id,
                    'employee_name': c.employee.name,
                    'end_date': c.end_date.strftime('%Y-%m-%d'),
                    'days_left': (c.end_date - today).days
                } for c in expiring_contracts],
                'unconfirmed_schedules': [{
                    'id': s.id,
                    'employee_name': s.employee.name,
                    'date': s.date.strftime('%Y-%m-%d'),
                    'start_time': s.start_time.strftime('%H:%M'),
                    'end_time': s.end_time.strftime('%H:%M')
                } for s in unconfirmed_schedules],
                'low_inventory': [{
                    'id': i.id,
                    'name': i.name,
                    'quantity': i.quantity,
                    'unit': i.unit,
                    'min_quantity': i.min_quantity
                } for i in low_inventory],
                'recent_feedbacks': [{
                    'id': f.id,
                    'rating': f.rating,
                    'comment': f.comment,
                    'submitted_at': f.submitted_at.strftime('%Y-%m-%d %H:%M')
                } for f in feedbacks],
                'feedback_analysis': feedback_analysis,
                'monthly_salary_total': round(total_salary, 2),
                'monthly_salary_period': {
                    'start': first_day.strftime('%Y-%m-%d'),
                    'end': last_day.strftime('%Y-%m-%d')
                }
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'대시보드 데이터 조회 중 오류 발생: {str(e)}'
        }), 500

@dashboard_bp.route('/api/dashboard/feedback', methods=['GET'])
def dashboard_feedback():
    """서비스 평가 대시보드"""
    try:
        # 기간 설정 (최근 30일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 피드백 데이터 조회
        feedbacks = WorkFeedback.query.join(
            Schedule, WorkFeedback.schedule_id == Schedule.id
        ).join(
            User, Schedule.user_id == User.id
        ).filter(
            WorkFeedback.submitted_at >= start_date,
            WorkFeedback.submitted_at <= end_date
        ).order_by(desc(WorkFeedback.submitted_at)).all()

        # 기본 통계
        total = len(feedbacks)
        avg_rating = sum(f.rating for f in feedbacks) / total if total > 0 else 0
        
        # 평점 분포
        rating_distribution = {
            1: 0, 2: 0, 3: 0, 4: 0, 5: 0
        }
        for f in feedbacks:
            rating_distribution[f.rating] += 1

        # 키워드 분석
        keywords = {}
        for f in feedbacks:
            if f.comment:
                words = f.comment.split()
                for word in words:
                    if len(word) > 1:  # 한 글자 제외
                        keywords[word] = keywords.get(word, 0) + 1

        # 상위 10개 키워드
        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]

        # 직원별 평균 평점
        employee_ratings = {}
        for f in feedbacks:
            employee = Employee.query.filter_by(user_id=f.schedule.user_id).first()
            if employee:
                if employee.user_id not in employee_ratings:
                    employee_ratings[employee.user_id] = {
                        'name': employee.user.name,
                        'total_rating': 0,
                        'count': 0
                    }
                employee_ratings[employee.user_id]['total_rating'] += f.rating
                employee_ratings[employee.user_id]['count'] += 1

        for emp_id in employee_ratings:
            emp = employee_ratings[emp_id]
            emp['average_rating'] = round(emp['total_rating'] / emp['count'], 1)

        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'statistics': {
                'total_feedbacks': total,
                'average_rating': round(avg_rating, 1),
                'rating_distribution': rating_distribution
            },
            'keywords': {
                'top_keywords': [{'word': k, 'count': v} for k, v in top_keywords]
            },
            'employee_performance': {
                'top_employees': sorted(
                    employee_ratings.values(),
                    key=lambda x: x['average_rating'],
                    reverse=True
                )[:5]
            },
            'recent_feedbacks': [{
                'id': f.id,
                'employee_name': f.schedule.user.name,
                'rating': f.rating,
                'comment': f.comment,
                'submitted_at': f.submitted_at.isoformat()
            } for f in feedbacks[:5]]
        })

    except Exception as e:
        logger.error(f"피드백 대시보드 생성 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'피드백 대시보드 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@dashboard_bp.route('/api/contract/analysis', methods=['POST'])
def contract_analysis():
    """계약서 분석"""
    try:
        data = request.get_json()
        contract_text = data.get('contract_text')
        
        if not contract_text:
            return jsonify({
                'status': 'error',
                'message': '계약서 텍스트가 필요합니다.'
            }), 400
            
        # 계약서 분석
        analysis = analyze_contract_text(contract_text)
        
        if analysis['status'] == 'error':
            return jsonify(analysis), 500
            
        return jsonify({
            'status': 'success',
            'data': {
                'analysis': analysis['analysis']
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'계약서 분석 중 오류 발생: {str(e)}'
        }), 500

@dashboard_bp.route('/api/attendance/lateness-analysis', methods=['GET'])
def lateness_analysis():
    """지각 기록 분석"""
    try:
        # 기간 필터링 파라미터
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 기본 쿼리
        query = Attendance.query.join(Schedule).filter(
            Attendance.clock_in.isnot(None),
            Schedule.start_time.isnot(None)
        )
        
        # 기간 필터링 적용
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Attendance.date <= end_date)
        
        # 지각 기록 조회 (최근 30일)
        if not start_date and not end_date:
            thirty_days_ago = datetime.now() - timedelta(days=30)
            query = query.filter(Attendance.date >= thirty_days_ago)
        
        attendance_logs = query.order_by(Attendance.date.desc()).all()
        
        # 지각 분석
        analysis = analyze_lateness(attendance_logs)
        
        if analysis['status'] == 'error':
            return jsonify(analysis), 500
            
        return jsonify({
            'status': 'success',
            'data': {
                'analysis': analysis['analysis'],
                'period': {
                    'start': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end': end_date.strftime('%Y-%m-%d') if end_date else None
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'지각 기록 분석 중 오류 발생: {str(e)}'
        }), 500

@dashboard_bp.route('/api/report/store', methods=['GET'])
def store_report():
    """매장 운영 리포트 생성"""
    try:
        # 기간 필터링 파라미터
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        # 분석 기간 설정
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 1. 인건비 및 근무 현황
        total_salary = 0
        work_hours = {}
        employees = User.query.filter_by(role='employee').all()
        
        for employee in employees:
            try:
                result = calculate_salary(employee.id, str(start_date), str(end_date))
                total_salary += result['calculated_salary']
                
                # 근무 시간 계산
                attendances = Attendance.query.filter(
                    Attendance.user_id == employee.id,
                    Attendance.date.between(start_date, end_date)
                ).all()
                
                total_hours = sum(
                    (a.clock_out - a.clock_in).total_seconds() / 3600
                    for a in attendances
                    if a.clock_in and a.clock_out
                )
                work_hours[employee.name] = round(total_hours, 2)
            except Exception as e:
                logger.error(f"급여 계산 오류: {employee.name} ({str(e)})")
                continue
        
        # 2. 인력 관리 현황
        expiring_contracts = Contract.query.filter(
            Contract.end_date.between(start_date, end_date)
        ).count()
        
        # 3. 재고 현황
        low_inventory = InventoryItem.query.filter(
            InventoryItem.quantity <= InventoryItem.min_quantity
        ).all()
        
        # 4. 피드백 현황
        feedbacks = WorkFeedback.query.filter(
            WorkFeedback.submitted_at.between(start_date, end_date)
        ).all()
        
        # 데이터 요약 생성
        data_summary = f"""
1. 인건비 및 근무 현황
- 총 인건비: {total_salary:,.0f}원
- 직원별 근무 시간:
{chr(10).join(f"- {name}: {hours}시간" for name, hours in work_hours.items())}

2. 인력 관리 현황
- 계약 만료 예정: {expiring_contracts}명
- 총 직원 수: {len(employees)}명

3. 재고 현황
- 재고 부족 품목: {len(low_inventory)}개
{chr(10).join(f"- {item.name}: {item.quantity}{item.unit} (최소 {item.min_quantity}{item.unit})" for item in low_inventory)}

4. 피드백 현황
- 총 피드백 수: {len(feedbacks)}건
- 평균 평점: {sum(f.rating for f in feedbacks) / len(feedbacks) if feedbacks else 0:.1f}점
"""
        
        # 리포트 생성
        report = generate_store_report(data_summary)
        
        if report['status'] == 'error':
            return jsonify(report), 500
            
        return jsonify({
            'status': 'success',
            'data': {
                'report': report['report'],
                'period': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'summary': data_summary
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'매장 리포트 생성 중 오류 발생: {str(e)}'
        }), 500 