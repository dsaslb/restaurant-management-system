from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from models import Employee, db
from datetime import datetime, date
from routes.auth import token_required
from flask_login import login_required, current_user
from models.attendance import Attendance  # Attendance 모델을 가정

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')

@employees_bp.route('/', methods=['GET'])
@login_required
def index():
    # 전체 직원 정보
    employees = Employee.query.order_by(Employee.name).all()

    # 오늘 날짜 기준 출퇴근 기록 조회
    today = date.today()
    attendance_map = {}
    records = Attendance.query.filter_by(date=today).all()
    for att in records:
        attendance_map[att.user_id] = att

    # 현재 사용자가 관리자 권한인지 확인
    is_admin = current_user.permissions.get('manage_users', False)

    return render_template(
        'employees/index.html',
        employees=employees,
        attendance_map=attendance_map,
        is_admin=is_admin
    )

@employees_bp.route('/employees', methods=['GET', 'POST'])
@token_required
def manage_employees(user_id):
    if request.method == 'POST':
        try:
            data = request.form
            new_emp = Employee(
                name=data.get('name'),
                age=int(data.get('age')),
                rrn=data.get('rrn'),
                address=data.get('address'),
                health_cert_date=datetime.strptime(data.get('health_cert_date'), '%Y-%m-%d'),
                phone=data.get('phone'),
                store_id=request.form.get('store_id')
            )
            
            db.session.add(new_emp)
            db.session.commit()
            flash('직원 등록 완료!')
        except Exception as e:
            flash('직원 등록 실패')
            return jsonify({'status': 'error', 'message': str(e)}), 500

    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@employees_bp.route('/api/employees', methods=['GET'])
@token_required
def get_employees(user_id):
    employees = Employee.query.all()
    return jsonify([{
        'id': emp.id,
        'name': emp.name,
        'age': emp.age,
        'phone': emp.phone,
        'store_id': emp.store_id
    } for emp in employees])

@employees_bp.route('/api/employees/<int:employee_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def employee_detail(user_id, employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': employee.id,
            'name': employee.name,
            'age': employee.age,
            'rrn': employee.rrn,
            'address': employee.address,
            'health_cert_date': employee.health_cert_date.isoformat(),
            'phone': employee.phone,
            'store_id': employee.store_id
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            for key, value in data.items():
                if hasattr(employee, key):
                    if key == 'health_cert_date':
                        value = datetime.strptime(value, '%Y-%m-%d')
                    setattr(employee, key, value)
            
            db.session.commit()
            return jsonify({'status': 'success', 'message': '직원 정보가 수정되었습니다.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(employee)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '직원이 삭제되었습니다.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500 