from datetime import datetime, timedelta
from models import Attendance, Employee, Contract, WorkEvaluation
from sqlalchemy import func, and_
from utils.wage import calculate_monthly_wage

def get_attendance_stats(store_id=None, start_date=None, end_date=None):
    """근무 통계 조회
    
    Args:
        store_id (int, optional): 매장 ID
        start_date (date, optional): 시작일
        end_date (date, optional): 종료일
        
    Returns:
        dict: 근무 통계 데이터
    """
    # 기본 기간 설정
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    # 쿼리 조건
    conditions = [
        Attendance.work_date >= start_date,
        Attendance.work_date <= end_date
    ]
    
    if store_id:
        conditions.append(Attendance.store_id == store_id)
        
    # 근무 데이터 조회
    attendances = Attendance.query.filter(*conditions).all()
    
    # 통계 계산
    total_hours = sum(
        ((a.clock_out - a.clock_in).total_seconds() / 3600)
        for a in attendances if a.clock_in and a.clock_out
    )
    
    total_employees = Employee.query.filter(
        Employee.store_id == store_id if store_id else True
    ).count()
    
    return {
        'total_employees': total_employees,
        'total_attendance': len(attendances),
        'total_hours': round(total_hours, 1),
        'avg_hours_per_day': round(total_hours / len(attendances) if attendances else 0, 1)
    }

def get_wage_stats(store_id=None):
    """급여 통계 조회
    
    Args:
        store_id (int, optional): 매장 ID
        
    Returns:
        dict: 급여 통계 데이터
    """
    # 직원 조회
    employees = Employee.query.filter(
        Employee.store_id == store_id if store_id else True
    ).all()
    
    total_wage = 0
    wage_by_type = {}
    
    for emp in employees:
        contract = Contract.query.filter_by(employee_id=emp.id).order_by(Contract.created_at.desc()).first()
        if contract:
            # 근무 시간 계산
            hours = sum(
                ((a.clock_out - a.clock_in).total_seconds() / 3600)
                for a in emp.attendances if a.clock_in and a.clock_out
            )
            
            # 급여 계산
            if contract.pay_type == '시급제':
                wage = contract.wage * hours
            else:  # 월급제
                wage = contract.wage
                
            total_wage += wage
            
            # 급여 유형별 집계
            if contract.pay_type not in wage_by_type:
                wage_by_type[contract.pay_type] = 0
            wage_by_type[contract.pay_type] += wage
            
    return {
        'total_wage': total_wage,
        'wage_by_type': wage_by_type
    }

def get_evaluation_stats(store_id=None, start_date=None, end_date=None):
    """평가 통계 조회
    
    Args:
        store_id (int, optional): 매장 ID
        start_date (date, optional): 시작일
        end_date (date, optional): 종료일
        
    Returns:
        dict: 평가 통계 데이터
    """
    # 기본 기간 설정
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    # 쿼리 조건
    conditions = [
        WorkEvaluation.submitted_at >= start_date,
        WorkEvaluation.submitted_at <= end_date
    ]
    
    if store_id:
        conditions.append(WorkEvaluation.store_id == store_id)
        
    # 평가 데이터 조회
    evaluations = WorkEvaluation.query.filter(*conditions).all()
    
    # 통계 계산
    total_evaluations = len(evaluations)
    avg_intensity = sum(e.intensity for e in evaluations) / total_evaluations if evaluations else 0
    
    return {
        'total_evaluations': total_evaluations,
        'avg_intensity': round(avg_intensity, 1)
    } 