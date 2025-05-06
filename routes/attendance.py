from flask import Blueprint, request, jsonify, render_template, session, send_file
from flask_login import login_required, current_user
from models import Attendance, User, db, Employee, Contract, WorkEvaluation, Notification
from utils.attendance import get_last_attendance
from utils.wage import calculate_monthly_wage
from utils.pdf import generate_payroll_pdf, generate_evaluation_pdf
from utils.statistics import get_attendance_stats, get_wage_stats, get_evaluation_stats
from utils.contract import renew_contract
from datetime import datetime, timedelta
from routes.auth import token_required
from utils.decorators import admin_required
from utils.response import api_response
from sqlalchemy import or_
import os
import logging
from flask import flash, redirect, url_for

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/api/attendance/<int:user_id>/clock-in', methods=['POST'])
@token_required
def clock_in(user_id):
    try:
        today = datetime.now().date()
        existing = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.func.date(Attendance.timestamp) == today
        ).first()
        
        if existing and existing.clock_in:
            return jsonify({'status': 'error', 'message': '이미 출근했습니다.'}), 400
            
        attendance = Attendance(
            user_id=user_id,
            timestamp=datetime.now(),
            clock_in=datetime.now().time()
        )
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '출근이 기록되었습니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@attendance_bp.route('/api/attendance/<int:user_id>/clock-out', methods=['POST'])
@token_required
def clock_out(user_id):
    try:
        today = datetime.now().date()
        attendance = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.func.date(Attendance.timestamp) == today
        ).first()
        
        if not attendance:
            return jsonify({'status': 'error', 'message': '출근 기록이 없습니다.'}), 400
            
        if attendance.clock_out:
            return jsonify({'status': 'error', 'message': '이미 퇴근했습니다.'}), 400
            
        attendance.clock_out = datetime.now().time()
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '퇴근이 기록되었습니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@attendance_bp.route('/api/attendance/<int:user_id>', methods=['GET'])
@token_required
def get_attendance(user_id):
    try:
        last_attendance = get_last_attendance(user_id)
        return jsonify({
            'status': 'success',
            'data': last_attendance
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@attendance_bp.route('/my_pay')
@login_required
def my_pay():
    """직원 급여 조회 페이지"""
    try:
        # 현재 직원 정보 조회
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if not employee:
            return render_template('error.html', message='직원 정보를 찾을 수 없습니다.'), 404

        # 현재 연도와 월
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)

        # 급여 계산
        wage_info = calculate_monthly_wage(employee.id, year, month)
        
        return render_template(
            'attendance/my_pay.html',
            wage_info=wage_info,
            year=year,
            month=month,
            employee=employee
        )
        
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@attendance_bp.route('/admin/paylist')
@login_required
@admin_required
def pay_list():
    """관리자 급여 목록 페이지"""
    try:
        # 검색 파라미터
        search = request.args.get('search', '')
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)

        # 직원 검색
        query = Employee.query
        if search:
            query = query.filter(
                or_(
                    Employee.name.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%')
                )
            )

        employees = query.all()
        pay_list = []

        for employee in employees:
            try:
                wage_info = calculate_monthly_wage(employee.id, year, month)
                pay_list.append({
                    'employee': employee,
                    'wage_info': wage_info
                })
            except Exception as e:
                logging.error(f"급여 계산 중 오류 발생 (직원 ID: {employee.id}): {str(e)}")
                pay_list.append({
                    'employee': employee,
                    'wage_info': {'error': '급여 계산 중 오류가 발생했습니다.'}
                })

        return render_template(
            'attendance/pay_list.html',
            pay_list=pay_list,
            year=year,
            month=month,
            search=search
        )
        
    except Exception as e:
        logging.error(f"급여 목록 조회 중 오류 발생: {str(e)}")
        flash('급여 목록을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@attendance_bp.route('/api/pay/<int:employee_id>')
@login_required
@admin_required
def get_employee_pay(employee_id):
    """직원 급여 정보 API"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year or not month:
            return api_response(
                status='error',
                message='연도와 월을 지정해주세요.',
                status_code=400
            )

        # 직원 존재 여부 확인
        employee = Employee.query.get_or_404(employee_id)
        
        # 급여 계산
        wage_info = calculate_monthly_wage(employee_id, year, month)
        
        return api_response(
            status='success',
            data=wage_info
        )
        
    except Exception as e:
        logging.error(f"급여 정보 조회 중 오류 발생 (직원 ID: {employee_id}): {str(e)}")
        return api_response(
            status='error',
            message='급여 정보를 불러오는데 실패했습니다.',
            status_code=500
        )

@attendance_bp.route('/api/pay/<int:employee_id>/pdf')
@login_required
def download_payroll_pdf(employee_id):
    """급여 명세서 PDF 다운로드"""
    try:
        # 권한 확인
        if not current_user.is_admin and current_user.employee.id != employee_id:
            return api_response(
                status='error',
                message='권한이 없습니다.',
                status_code=403
            )

        # 파라미터 확인
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year or not month:
            return api_response(
                status='error',
                message='연도와 월을 지정해주세요.',
                status_code=400
            )

        # 직원 정보 조회
        employee = Employee.query.get_or_404(employee_id)
        
        # 급여 정보 계산
        wage_info = calculate_monthly_wage(employee_id, year, month)
        
        # PDF 파일 경로
        pdf_dir = os.path.join('static', 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"payroll_{employee_id}_{year}_{month}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)
        
        # PDF 생성
        if not generate_payroll_pdf(employee, wage_info, year, month, pdf_path):
            raise Exception("PDF 생성에 실패했습니다.")
        
        # PDF 파일 전송
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logging.error(f"급여 명세서 PDF 생성 중 오류 발생 (직원 ID: {employee_id}): {str(e)}")
        return api_response(
            status='error',
            message='급여 명세서 생성에 실패했습니다.',
            status_code=500
        )

@attendance_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """관리자 대시보드"""
    try:
        # 기간 설정
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 매장 ID (필요한 경우)
        store_id = request.args.get('store_id', type=int)
        
        # 통계 데이터 조회
        attendance_stats = get_attendance_stats(store_id, start_date, end_date)
        wage_stats = get_wage_stats(store_id)
        evaluation_stats = get_evaluation_stats(store_id, start_date, end_date)
        
        # 계약 만료 임박 직원 조회
        expiring_contracts = Contract.query.filter(
            Contract.end_date <= end_date + timedelta(days=30),
            Contract.end_date >= end_date
        ).all()
        
        # 알림 목록 조회
        notifications = Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        return render_template(
            'attendance/dashboard.html',
            attendance_stats=attendance_stats,
            wage_stats=wage_stats,
            evaluation_stats=evaluation_stats,
            expiring_contracts=expiring_contracts,
            notifications=notifications,
            start_date=start_date,
            end_date=end_date,
            store_id=store_id
        )
        
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@attendance_bp.route('/api/dashboard/stats')
@login_required
@admin_required
def get_dashboard_stats():
    """대시보드 통계 API"""
    try:
        # 파라미터
        store_id = request.args.get('store_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # 날짜 변환
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        # 통계 데이터 조회
        attendance_stats = get_attendance_stats(store_id, start_date, end_date)
        wage_stats = get_wage_stats(store_id, year, month)
        
        return api_response(
            status='success',
            data={
                'attendance': attendance_stats,
                'wage': wage_stats
            }
        )
        
    except Exception as e:
        return api_response(
            status='error',
            message=str(e),
            status_code=500
        )

@attendance_bp.route('/evaluation', methods=['POST'])
@login_required
def submit_evaluation():
    """근무 평가 제출"""
    try:
        data = request.get_json()
        work_intensity = data.get('work_intensity')
        feedback = data.get('feedback')
        
        if not work_intensity or not isinstance(work_intensity, int) or work_intensity < 1 or work_intensity > 5:
            return api_response(
                status='error',
                message='근무 강도는 1-5 사이의 정수여야 합니다.',
                status_code=400
            )
            
        # 오늘 날짜의 근무 기록 확인
        today = datetime.now().date()
        attendance = Attendance.query.filter_by(
            employee_id=current_user.id,
            work_date=today
        ).first()
        
        if not attendance:
            return api_response(
                status='error',
                message='오늘의 근무 기록이 없습니다.',
                status_code=400
            )
            
        # 이미 평가를 했는지 확인
        existing_eval = WorkEvaluation.query.filter_by(
            employee_id=current_user.id,
            work_date=today
        ).first()
        
        if existing_eval:
            return api_response(
                status='error',
                message='이미 오늘의 근무 평가를 제출했습니다.',
                status_code=400
            )
            
        # 평가 저장
        evaluation = WorkEvaluation(
            employee_id=current_user.id,
            work_date=today,
            work_intensity=work_intensity,
            feedback=feedback
        )
        
        db.session.add(evaluation)
        db.session.commit()
        
        return api_response(
            status='success',
            message='근무 평가가 저장되었습니다.',
            data=evaluation.to_dict()
        )
        
    except Exception as e:
        return api_response(
            status='error',
            message=str(e),
            status_code=500
        )

@attendance_bp.route('/admin/evaluations')
@login_required
@admin_required
def view_evaluations():
    """관리자용 근무 평가 조회"""
    try:
        # 파라미터
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        store_id = request.args.get('store_id', type=int)
        
        # 날짜 변환
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        # 통계 데이터 조회
        stats = get_evaluation_stats(store_id, start_date, end_date)
        
        return render_template(
            'attendance/evaluations.html',
            stats=stats,
            start_date=start_date,
            end_date=end_date,
            store_id=store_id
        )
        
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@attendance_bp.route('/admin/evaluations/pdf')
@login_required
@admin_required
def download_evaluation_pdf():
    """평가 보고서 PDF 다운로드"""
    try:
        # 파라미터
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        store_id = request.args.get('store_id', type=int)
        show_anonymous = request.args.get('show_anonymous', 'true') == 'true'
        
        # 날짜 변환
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        # 통계 데이터 조회
        stats = get_evaluation_stats(store_id, start_date, end_date, show_anonymous)
        
        # PDF 생성
        pdf_path = generate_evaluation_pdf(stats)
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'evaluation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        return api_response(
            status='error',
            message=str(e),
            status_code=500
        )

@attendance_bp.route('/api/contracts/<int:contract_id>/renew', methods=['POST'])
@login_required
@admin_required
def renew_contract_api(contract_id):
    """계약 갱신 API"""
    try:
        data = request.get_json()
        new_end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        if not new_end_date:
            return api_response(
                status='error',
                message='새로운 종료일을 지정해주세요.',
                status_code=400
            )
            
        # 계약 갱신
        contract = renew_contract(
            contract_id=contract_id,
            new_end_date=new_end_date,
            renewed_by=current_user.id
        )
        
        return api_response(
            status='success',
            message='계약이 갱신되었습니다.',
            data=contract.to_dict()
        )
        
    except Exception as e:
        return api_response(
            status='error',
            message=str(e),
            status_code=500
        ) 