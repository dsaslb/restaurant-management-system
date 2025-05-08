from datetime import datetime, timedelta
from models.employee import Employee, Attendance, Payroll
from extensions import db

def calculate_work_duration(check_in, check_out):
    """
    출근/퇴근 시간을 받아 실 근무 시간(분)을 계산한다.
    :param check_in: str ('HH:MM:SS')
    :param check_out: str ('HH:MM:SS')
    :return: int (minutes)
    """
    fmt = "%H:%M:%S"
    start = datetime.strptime(check_in, fmt)
    end = datetime.strptime(check_out, fmt)
    duration = (end - start).total_seconds() / 60
    return int(duration)

def calculate_salary(work_minutes, pay_type, base_pay):
    """
    근무 시간과 급여제에 따라 급여를 계산한다.
    :param work_minutes: int, 총 근무 시간 (분)
    :param pay_type: str, '시급제', '월급제', '주급제'
    :param base_pay: float, 기준 금액 (시급, 월급, 주급)
    :return: float, 계산된 급여
    """
    if pay_type == '시급제':
        hours = work_minutes / 60
        return round(hours * base_pay, 2)
    elif pay_type == '주급제':
        return base_pay  # 주 단위 정산 예정
    elif pay_type == '월급제':
        return base_pay  # 고정 지급
    else:
        raise ValueError("지원되지 않는 급여제 유형입니다.")

def calculate_overtime_pay(work_minutes, base_pay):
    """
    야근수당을 계산한다.
    :param work_minutes: int, 총 근무 시간 (분)
    :param base_pay: float, 시급
    :return: float, 야근수당
    """
    standard_minutes = 8 * 60  # 8시간
    if work_minutes <= standard_minutes:
        return 0.0
    
    overtime_minutes = work_minutes - standard_minutes
    overtime_rate = 1.5  # 야근 수당 비율
    return round((overtime_minutes / 60) * base_pay * overtime_rate, 2)

def generate_monthly_payroll(employee_id, year, month):
    """
    월별 급여를 생성한다.
    :param employee_id: int, 직원 ID
    :param year: int, 연도
    :param month: int, 월
    :return: Payroll 객체
    """
    employee = Employee.query.get(employee_id)
    if not employee:
        raise ValueError("직원을 찾을 수 없습니다.")
    
    # 해당 월의 출근 기록 조회
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    attendances = Attendance.query.filter(
        Attendance.employee_id == employee_id,
        Attendance.date >= start_date.date(),
        Attendance.date <= end_date.date()
    ).all()
    
    # 총 근무 시간 계산
    total_work_minutes = sum(attendance.work_minutes or 0 for attendance in attendances)
    
    # 기본급 계산
    base_salary = calculate_salary(total_work_minutes, employee.pay_type, employee.base_pay)
    
    # 야근수당 계산
    overtime_pay = calculate_overtime_pay(total_work_minutes, employee.base_pay)
    
    # 급여 객체 생성
    payroll = Payroll(
        employee_id=employee_id,
        year=year,
        month=month,
        total_work_minutes=total_work_minutes,
        base_salary=base_salary,
        overtime_pay=overtime_pay,
        net_salary=base_salary + overtime_pay
    )
    
    db.session.add(payroll)
    db.session.commit()
    
    return payroll

def get_payroll_summary(employee_id, year, month):
    """
    급여 요약 정보를 반환한다.
    :param employee_id: int, 직원 ID
    :param year: int, 연도
    :param month: int, 월
    :return: dict, 급여 요약 정보
    """
    payroll = Payroll.query.filter_by(
        employee_id=employee_id,
        year=year,
        month=month
    ).first()
    
    if not payroll:
        return None
    
    return {
        'employee_id': payroll.employee_id,
        'year': payroll.year,
        'month': payroll.month,
        'total_work_minutes': payroll.total_work_minutes,
        'base_salary': payroll.base_salary,
        'overtime_pay': payroll.overtime_pay,
        'bonus': payroll.bonus,
        'deductions': payroll.deductions,
        'net_salary': payroll.net_salary,
        'payment_date': payroll.payment_date,
        'payment_status': payroll.payment_status
    } 