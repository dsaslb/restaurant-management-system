from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Employee, Contract, Attendance, User
from datetime import datetime, timedelta
from utils.decorators import admin_required
from werkzeug.security import generate_password_hash
import logging

# Blueprint 객체 생성
employee_bp = Blueprint('employee', __name__, url_prefix='/employee')
logger = logging.getLogger(__name__)

@employee_bp.route('/')
@login_required
def index():
    """직원 목록 페이지"""
    employees = Employee.query.all()
    return render_template('employee/list.html', employees=employees)

@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    """직원 추가"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        phone = request.form.get('phone')
        position = request.form.get('position')
        hourly_wage = float(request.form.get('hourly_wage', 0))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        # 사용자 계정 생성
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.flush()
        
        # 직원 정보 생성
        employee = Employee(
            user_id=user.id,
            name=name,
            phone=phone,
            position=position
        )
        db.session.add(employee)
        db.session.flush()
        
        # 계약 정보 생성
        contract = Contract(
            employee_id=employee.id,
            hourly_wage=hourly_wage,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(contract)
        
        try:
            db.session.commit()
            flash('직원이 성공적으로 추가되었습니다.', 'success')
            return redirect(url_for('employee.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'오류가 발생했습니다: {str(e)}', 'error')
    
    return render_template('employee/add.html')

@employee_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    """직원 정보 수정"""
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        employee.name = request.form.get('name')
        employee.phone = request.form.get('phone')
        employee.position = request.form.get('position')
        
        # 계약 정보 업데이트
        contract = employee.current_contract
        if contract:
            contract.hourly_wage = float(request.form.get('hourly_wage', 0))
            contract.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            contract.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        try:
            db.session.commit()
            flash('직원 정보가 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('employee.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'오류가 발생했습니다: {str(e)}', 'error')
    
    return render_template('employee/edit.html', employee=employee)

@employee_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    """근태 기록"""
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        check_type = request.form.get('check_type')
        
        attendance = Attendance.query.filter_by(
            employee_id=employee_id,
            date=datetime.now().date()
        ).first()
        
        if not attendance:
            attendance = Attendance(employee_id=employee_id, date=datetime.now().date())
            db.session.add(attendance)
        
        if check_type == 'in':
            attendance.check_in = datetime.now()
        else:
            attendance.check_out = datetime.now()
        
        db.session.commit()
        flash('출근/퇴근이 기록되었습니다.', 'success')
        return redirect(url_for('employee.attendance'))
    
    employees = Employee.query.all()
    return render_template('employee/attendance.html', employees=employees)

@employee_bp.route('/attendance/history')
@login_required
def attendance_history():
    """근태 기록 조회"""
    attendances = Attendance.query.order_by(Attendance.date.desc()).all()
    return render_template('employee/attendance_history.html', attendances=attendances)

@employee_bp.route('/contract/renew/<int:id>', methods=['POST'])
@login_required
@admin_required
def renew_contract(id):
    """계약 갱신"""
    employee = Employee.query.get_or_404(id)
    data = request.get_json()
    
    contract = Contract(
        employee_id=employee.id,
        hourly_wage=data['hourly_wage'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    )
    
    db.session.add(contract)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '계약이 갱신되었습니다.',
        'contract': {
            'id': contract.id,
            'hourly_wage': contract.hourly_wage,
            'start_date': contract.start_date.strftime('%Y-%m-%d'),
            'end_date': contract.end_date.strftime('%Y-%m-%d')
        }
    })

@employee_bp.route('/admin/employees')
@login_required
@admin_required
def admin_employees():
    """직원 목록 조회"""
    try:
        employees = Employee.query.all()
        return render_template('employee/admin/list.html', employees=employees)
    except Exception as e:
        logger.error(f"직원 목록 조회 중 오류 발생: {str(e)}")
        flash('직원 목록을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@employee_bp.route('/admin/employees/<int:employee_id>')
@login_required
@admin_required
def admin_employee_detail(employee_id):
    """직원 상세 정보 조회"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        return render_template('employee/admin/detail.html', employee=employee)
    except Exception as e:
        logger.error(f"직원 상세 정보 조회 중 오류 발생: {str(e)}")
        flash('직원 정보를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('employee.admin_employees')) 