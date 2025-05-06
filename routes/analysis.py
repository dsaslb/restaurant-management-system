from flask import Blueprint, request, jsonify, send_file
from models import db, User, StoreReport, WorkFeedback, Schedule, Contract, InventoryItem, Attendance, Store, Employee
from utils.gpt_analysis import analyze_feedback, analyze_contract, analyze_lateness, generate_store_report
from utils.pdf import generate_store_report_pdf
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
import os
from sqlalchemy import and_, func, case
from utils.salary_utils import calculate_salary

analysis_bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)

@analysis_bp.route('/api/report/ai', methods=['POST'])
@jwt_required()
def analyze_and_save():
    """AI 기반 종합 리포트 생성 및 저장"""
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
            
        # 요청 데이터 검증
        data = request.get_json()
        if not data or 'summary_text' not in data:
            return jsonify({
                'status': 'error',
                'message': '분석할 데이터가 필요합니다.'
            }), 400
            
        summary_data = data['summary_text']
        
        # AI 리포트 생성
        result = generate_store_report(summary_data)
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'AI 리포트 생성에 실패했습니다.'
            }), 500
            
        # PDF 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ai_store_summary_{timestamp}'
        filepath = generate_store_report_pdf(result, filename)
        
        if not filepath:
            return jsonify({
                'status': 'error',
                'message': 'PDF 생성에 실패했습니다.'
            }), 500
            
        # 리포트 저장
        report = StoreReport(
            user_id=current_user_id,
            summary=result,
            pdf_path=filepath,
            created_at=datetime.utcnow()
        )
        
        db.session.add(report)
        db.session.commit()
        
        logger.info(f"AI 리포트 생성 완료: report_id={report.id}")
        
        return jsonify({
            'status': 'success',
            'message': '리포트가 성공적으로 생성되었습니다.',
            'report_id': report.id,
            'pdf_path': filepath,
            'summary': result
        })
        
    except Exception as e:
        logger.error(f"AI 리포트 생성 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'리포트 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@analysis_bp.route('/api/report/<int:report_id>/download', methods=['GET'])
@jwt_required()
def download_report(report_id):
    """리포트 PDF 다운로드"""
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
            
        # 리포트 조회
        report = StoreReport.query.get_or_404(report_id)
        
        if not report.pdf_path or not os.path.exists(report.pdf_path):
            return jsonify({
                'status': 'error',
                'message': 'PDF 파일을 찾을 수 없습니다.'
            }), 404
            
        return send_file(
            report.pdf_path,
            as_attachment=True,
            download_name=f'store_report_{report_id}.pdf'
        )
        
    except Exception as e:
        logger.error(f"리포트 다운로드 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'리포트 다운로드 중 오류가 발생했습니다: {str(e)}'
        }), 500

@analysis_bp.route('/api/attendance/analysis', methods=['GET'])
def analyze_attendance():
    """출석 분석"""
    try:
        # 기간 설정 (최근 30일)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 출석 데이터 조회
        logs = Attendance.query.join(
            Schedule, Attendance.schedule_id == Schedule.id
        ).join(
            User, Schedule.user_id == User.id
        ).filter(
            and_(
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).all()

        late_list = []
        overwork_list = []
        absence_list = []

        for log in logs:
            # 지각 체크 (10분 이상)
            scheduled_start = datetime.strptime(log.schedule.start_time, '%H:%M').time()
            if log.clock_in.time() > (datetime.combine(log.date, scheduled_start) + timedelta(minutes=10)).time():
                late_list.append({
                    'user_id': log.schedule.user_id,
                    'user_name': log.schedule.user.name,
                    'date': log.date.isoformat(),
                    'scheduled_time': log.schedule.start_time,
                    'actual_time': log.clock_in.time().strftime('%H:%M')
                })

            # 연장 근무 체크 (30분 이상)
            if log.clock_out and log.schedule:
                scheduled_end = datetime.strptime(log.schedule.end_time, '%H:%M').time()
                if log.clock_out.time() > (datetime.combine(log.date, scheduled_end) + timedelta(minutes=30)).time():
                    overwork_list.append({
                        'user_id': log.schedule.user_id,
                        'user_name': log.schedule.user.name,
                        'date': log.date.isoformat(),
                        'scheduled_time': log.schedule.end_time,
                        'actual_time': log.clock_out.time().strftime('%H:%M')
                    })

        # 결근 체크
        scheduled_days = Schedule.query.filter(
            and_(
                Schedule.date >= start_date,
                Schedule.date <= end_date
            )
        ).all()
        
        for schedule in scheduled_days:
            attendance = Attendance.query.filter_by(
                schedule_id=schedule.id
            ).first()
            
            if not attendance or not attendance.clock_in:
                absence_list.append({
                    'user_id': schedule.user_id,
                    'user_name': schedule.user.name,
                    'date': schedule.date.isoformat()
                })

        # 통계 계산
        total_work_days = len(logs)
        late_rate = (len(late_list) / total_work_days * 100) if total_work_days > 0 else 0
        overwork_rate = (len(overwork_list) / total_work_days * 100) if total_work_days > 0 else 0
        absence_rate = (len(absence_list) / len(scheduled_days) * 100) if scheduled_days else 0

        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'statistics': {
                'total_work_days': total_work_days,
                'late_count': len(late_list),
                'overwork_count': len(overwork_list),
                'absence_count': len(absence_list),
                'late_rate': round(late_rate, 1),
                'overwork_rate': round(overwork_rate, 1),
                'absence_rate': round(absence_rate, 1)
            },
            'details': {
                'late_list': late_list[:5],
                'overwork_list': overwork_list[:5],
                'absence_list': absence_list[:5]
            }
        })

    except Exception as e:
        logger.error(f"출석 분석 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'출석 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@analysis_bp.route('/api/kpi/<string:store_name>', methods=['GET'])
def store_kpi(store_name):
    """매장별 KPI 분석"""
    try:
        # 매장 존재 확인
        store = Store.query.filter_by(name=store_name).first_or_404()

        # 기간 설정 (최근 3개월)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        # 1. 인원 현황
        total_employees = User.query.join(Employee).filter(
            Employee.store_id == store.id
        ).count()

        active_employees = User.query.join(Employee).filter(
            and_(
                Employee.store_id == store.id,
                Employee.status == 'active'
            )
        ).count()

        # 2. 근무 현황
        attendance_stats = db.session.query(
            func.avg(func.julianday(Attendance.clock_out) - func.julianday(Attendance.clock_in)).label('avg_hours'),
            func.count(Attendance.id).label('total_attendances'),
            func.count(case([(Attendance.clock_in > Schedule.start_time + timedelta(minutes=10), 1)])).label('late_count')
        ).join(
            Schedule, Attendance.schedule_id == Schedule.id
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            and_(
                Employee.store_id == store.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).first()

        avg_work_hours = round(attendance_stats.avg_hours * 24, 2) if attendance_stats.avg_hours else 0
        late_rate = round(attendance_stats.late_count / attendance_stats.total_attendances * 100, 1) if attendance_stats.total_attendances else 0

        # 3. 급여 현황
        salaries = []
        for employee in Employee.query.filter_by(store_id=store.id).all():
            try:
                salary_data = calculate_salary(
                    employee.user_id,
                    start_date,
                    end_date
                )
                salaries.append(salary_data['payments']['total_salary'])
            except Exception as e:
                logger.error(f"급여 계산 오류: {employee.user.name} ({str(e)})")
                continue

        avg_salary = round(sum(salaries) / len(salaries)) if salaries else 0

        # 4. 피드백 현황
        feedback_stats = db.session.query(
            func.avg(WorkFeedback.rating).label('avg_rating'),
            func.count(WorkFeedback.id).label('total_feedbacks')
        ).join(
            Schedule, WorkFeedback.schedule_id == Schedule.id
        ).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            and_(
                Employee.store_id == store.id,
                WorkFeedback.submitted_at >= start_date,
                WorkFeedback.submitted_at <= end_date
            )
        ).first()

        avg_rating = round(feedback_stats.avg_rating, 1) if feedback_stats.avg_rating else 0

        return jsonify({
            'store': {
                'name': store.name,
                'address': store.address,
                'phone': store.phone
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'employees': {
                'total': total_employees,
                'active': active_employees,
                'inactive': total_employees - active_employees
            },
            'attendance': {
                'avg_work_hours': avg_work_hours,
                'total_attendances': attendance_stats.total_attendances,
                'late_rate': late_rate
            },
            'salary': {
                'avg_salary': avg_salary,
                'total_payroll': sum(salaries) if salaries else 0
            },
            'feedback': {
                'avg_rating': avg_rating,
                'total_feedbacks': feedback_stats.total_feedbacks
            }
        })

    except Exception as e:
        logger.error(f"KPI 분석 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'KPI 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500 