from models import User, Attendance, UserContract, Store, Schedule, Holiday
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from extensions import db
import logging
import traceback
from holidays import KR
from sqlalchemy import and_

# 로거 설정
logger = logging.getLogger(__name__)

# 상수 정의
STANDARD_HOURS_PER_WEEK = 40  # 주 40시간 근무
STANDARD_HOURS_PER_DAY = 8    # 1일 8시간 근무
OVERTIME_RATE = 1.5          # 연장근무 수당 비율 (기본급의 50% 가산)
NIGHT_RATE = 1.5             # 야간근무 수당 비율 (기본급의 50% 가산)
HOLIDAY_RATE = 1.5           # 휴일근무 수당 비율 (기본급의 50% 가산)
HOLIDAY_OVERTIME_RATE = 2.0  # 휴일 연장근무 수당 비율 (기본급의 100% 가산)

# 4대보험 요율 (2024년 1월 기준)
NATIONAL_PENSION_RATE = 0.09        # 국민연금 9% (근로자 4.5%, 사업주 4.5%)
HEALTH_INSURANCE_RATE = 0.0699      # 건강보험 6.99% (근로자 3.495%, 사업주 3.495%)
LONG_TERM_CARE_RATE = 0.1304        # 장기요양 13.04% (건강보험료의 13.04%)
EMPLOYMENT_INSURANCE_RATE = 0.016   # 고용보험 1.6% (근로자 0.8%, 사업주 0.8%)

# 최저/최고 보험료 기준 (2024년 기준)
MIN_MONTHLY_SALARY = 2_000_000      # 최저 월급여액
MAX_MONTHLY_SALARY = 5_000_000      # 최고 월급여액

# 최저시급 (2024년 기준)
MINIMUM_WAGE = 9_860                # 2024년 최저시급 9,860원

# 공휴일 목록 (2024년)
PUBLIC_HOLIDAYS = KR()

# 수당 기준
MEAL_ALLOWANCE = 8000  # 1식당 8,000원
TRANSPORTATION_ALLOWANCE = 5000  # 1일당 5,000원

# 근로기준법 관련 상수
MAX_WEEKLY_HOURS = 52  # 주 최대 근로시간
MIN_REST_HOURS = 12  # 근로시간 사이 최소 휴식시간
MAX_DAILY_HOURS = 8  # 1일 최대 근로시간
MIN_REST_DAYS = 1  # 주 최소 휴식일

def get_holiday_name(date: datetime.date) -> Optional[str]:
    """공휴일 이름 반환"""
    return PUBLIC_HOLIDAYS.get(date)

def is_holiday(date: datetime.date) -> bool:
    """휴일 여부 확인 (토요일, 일요일, 공휴일)
    
    근로기준법 제55조: 1주일에 1일 이상의 유급휴일을 주어야 한다.
    """
    return date.weekday() >= 5 or date in PUBLIC_HOLIDAYS

def calculate_meal_allowance(work_hours: float) -> float:
    """식대 수당 계산"""
    if work_hours >= 8:
        return MEAL_ALLOWANCE * 2
    elif work_hours >= 4:
        return MEAL_ALLOWANCE
    return 0

def calculate_transportation_allowance(attendance_count: int) -> float:
    """교통비 수당 계산"""
    return TRANSPORTATION_ALLOWANCE * attendance_count

def calculate_insurance_premiums(salary: float, is_regular: bool = True) -> Dict:
    """4대보험료 계산 (2024년 기준)
    
    Args:
        salary (float): 월 급여액
        is_regular (bool): 정규직 여부 (True: 정규직, False: 비정규직)
        
    Returns:
        Dict: 4대보험료 상세 내역
    """
    if not is_regular:
        # 비정규직은 고용보험만 적용
        employment_insurance = salary * EMPLOYMENT_INSURANCE_RATE
        return {
            'national_pension': 0,
            'health_insurance': 0,
            'long_term_care': 0,
            'employment_insurance': round(employment_insurance, 2),
            'total_insurance': round(employment_insurance, 2)
        }
    
    # 보험료 산정 기준액 계산 (최저/최고 기준 적용)
    adjusted_salary = max(min(salary, MAX_MONTHLY_SALARY), MIN_MONTHLY_SALARY)
    
    # 국민연금 (9%)
    national_pension = adjusted_salary * NATIONAL_PENSION_RATE
    
    # 건강보험 (6.99%)
    health_insurance = adjusted_salary * HEALTH_INSURANCE_RATE
    
    # 장기요양 (건강보험료의 13.04%)
    long_term_care = health_insurance * LONG_TERM_CARE_RATE
    
    # 고용보험 (1.6%)
    employment_insurance = adjusted_salary * EMPLOYMENT_INSURANCE_RATE
    
    # 총 보험료
    total_insurance = national_pension + health_insurance + long_term_care + employment_insurance
    
    return {
        'national_pension': round(national_pension, 2),
        'health_insurance': round(health_insurance, 2),
        'long_term_care': round(long_term_care, 2),
        'employment_insurance': round(employment_insurance, 2),
        'total_insurance': round(total_insurance, 2)
    }

def is_night_shift(start_time: datetime, end_time: datetime) -> bool:
    """야간근무 여부 확인 (22:00-06:00)
    
    근로기준법 제53조: 야간근로는 오후 10시부터 오전 6시까지의 시간을 말한다.
    """
    night_start = start_time.replace(hour=22, minute=0, second=0)
    night_end = end_time.replace(hour=6, minute=0, second=0)
    return start_time >= night_start or end_time <= night_end

def calculate_overtime_pay(hours: float, wage: float) -> float:
    """연장근무 수당 계산
    
    근로기준법 제56조: 연장근로에 대해서는 통상임금의 50% 이상을 가산하여 지급
    """
    return hours * wage * OVERTIME_RATE

def calculate_night_pay(hours: float, wage: float) -> float:
    """야간근무 수당 계산
    
    근로기준법 제56조: 야간근로에 대해서는 통상임금의 50% 이상을 가산하여 지급
    """
    return hours * wage * NIGHT_RATE

def calculate_holiday_pay(hours: float, wage: float) -> float:
    """휴일근무 수당 계산
    
    근로기준법 제56조: 휴일근로에 대해서는 통상임금의 50% 이상을 가산하여 지급
    """
    return hours * wage * HOLIDAY_RATE

def calculate_holiday_overtime_pay(hours: float, wage: float) -> float:
    """휴일 연장근무 수당 계산
    
    근로기준법 제56조: 휴일의 연장근로에 대해서는 통상임금의 100% 이상을 가산하여 지급
    """
    return hours * wage * HOLIDAY_OVERTIME_RATE

def check_labor_standards_violations(attendances: List[Attendance]) -> Tuple[bool, List[str]]:
    """근로기준법 위반 체크"""
    violations = []
    
    # 주간 근로시간 체크
    weekly_hours = {}
    for att in attendances:
        week = att.clock_in.isocalendar()[1]
        if week not in weekly_hours:
            weekly_hours[week] = 0
        weekly_hours[week] += (att.clock_out - att.clock_in).total_seconds() / 3600
    
    for week, hours in weekly_hours.items():
        if hours > MAX_WEEKLY_HOURS:
            violations.append(f"주 {week}의 근로시간이 {hours:.1f}시간으로 주 최대 근로시간({MAX_WEEKLY_HOURS}시간)을 초과했습니다.")
    
    # 연속 근무 체크
    sorted_attendances = sorted(attendances, key=lambda x: x.clock_in)
    for i in range(len(sorted_attendances) - 1):
        rest_hours = (sorted_attendances[i+1].clock_in - sorted_attendances[i].clock_out).total_seconds() / 3600
        if rest_hours < MIN_REST_HOURS:
            violations.append(f"{sorted_attendances[i].clock_out.date()} 퇴근 후 {sorted_attendances[i+1].clock_in.date()} 출근까지의 휴식시간이 {rest_hours:.1f}시간으로 최소 휴식시간({MIN_REST_HOURS}시간) 미만입니다.")
    
    # 일일 근로시간 체크
    for att in attendances:
        daily_hours = (att.clock_out - att.clock_in).total_seconds() / 3600
        if daily_hours > MAX_DAILY_HOURS:
            violations.append(f"{att.clock_in.date()}의 근로시간이 {daily_hours:.1f}시간으로 일 최대 근로시간({MAX_DAILY_HOURS}시간)을 초과했습니다.")
    
    # 주간 휴식일 체크
    weekly_rest_days = {}
    for att in attendances:
        week = att.clock_in.isocalendar()[1]
        if week not in weekly_rest_days:
            weekly_rest_days[week] = set()
        weekly_rest_days[week].add(att.clock_in.date())
    
    for week, work_days in weekly_rest_days.items():
        if len(work_days) > 7 - MIN_REST_DAYS:
            violations.append(f"주 {week}의 근무일수가 {len(work_days)}일로 최소 휴식일({MIN_REST_DAYS}일) 미만입니다.")
    
    return len(violations) > 0, violations

def calculate_salary(user_id, start_date, end_date, hourly_rate=10000):
    """급여 계산"""
    try:
        # 근무 기록 조회
        logs = Attendance.query.join(
            Schedule, Attendance.schedule_id == Schedule.id
        ).filter(
            and_(
                Schedule.user_id == user_id,
                Schedule.date >= start_date,
                Schedule.date <= end_date
            )
        ).all()

        total_minutes = 0
        overtime_minutes = 0
        holiday_minutes = 0
        night_minutes = 0

        for log in logs:
            if not log.clock_in or not log.clock_out:
                continue

            # 근무 시간 계산
            duration = (log.clock_out - log.clock_in).total_seconds() / 60
            
            # 휴일 체크
            is_holiday = Holiday.query.filter_by(date=log.date).first()
            if is_holiday:
                holiday_minutes += duration
                continue

            # 야간 근무 체크 (22:00 ~ 06:00)
            night_start = datetime.combine(log.date, datetime.strptime('22:00', '%H:%M').time())
            night_end = datetime.combine(log.date + timedelta(days=1), datetime.strptime('06:00', '%H:%M').time())
            
            if log.clock_in < night_start and log.clock_out > night_start:
                night_duration = (log.clock_out - night_start).total_seconds() / 60
                night_minutes += night_duration
                duration -= night_duration
            
            if log.clock_in < night_end and log.clock_out > night_end:
                night_duration = (night_end - log.clock_in).total_seconds() / 60
                night_minutes += night_duration
                duration -= night_duration

            # 기본 근무 및 연장 근무 계산
            if duration > 480:  # 8시간 초과
                overtime_minutes += duration - 480
                total_minutes += 480
            else:
                total_minutes += duration

        # 급여 계산
        base_pay = (total_minutes / 60) * hourly_rate
        overtime_pay = (overtime_minutes / 60) * (hourly_rate * 1.5)
        holiday_pay = (holiday_minutes / 60) * (hourly_rate * 1.5)
        night_pay = (night_minutes / 60) * (hourly_rate * 1.3)

        total_salary = base_pay + overtime_pay + holiday_pay + night_pay

        return {
            'user_id': user_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'work_hours': {
                'base_hours': round(total_minutes / 60, 2),
                'overtime_hours': round(overtime_minutes / 60, 2),
                'holiday_hours': round(holiday_minutes / 60, 2),
                'night_hours': round(night_minutes / 60, 2)
            },
            'payments': {
                'base_pay': round(base_pay),
                'overtime_pay': round(overtime_pay),
                'holiday_pay': round(holiday_pay),
                'night_pay': round(night_pay),
                'total_salary': round(total_salary)
            }
        }

    except Exception as e:
        logger.error(f"급여 계산 중 오류 발생: {str(e)}")
        raise 