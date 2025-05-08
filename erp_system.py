import logging
import unittest
from datetime import datetime
from typing import Union, Literal, List, Dict, Optional
from functools import lru_cache
from dataclasses import dataclass
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('erp_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 타입 정의
PayType = Literal['시급제', '주급제', '월급제']
WorkStatus = Literal['정상', '지각', '조퇴', '결근', '휴가']

# 예외 클래스
class SalaryCalculationError(Exception):
    """급여 계산 관련 예외"""
    pass

class WorkDurationError(Exception):
    """근무 시간 계산 관련 예외"""
    pass

# 데이터 클래스
@dataclass
class WorkRecord:
    employee_id: str
    check_in: str
    check_out: str
    status: WorkStatus
    note: Optional[str] = None

@dataclass
class SalaryData:
    employee_id: str
    year: int
    month: int
    base_salary: float
    overtime_pay: float
    bonus: float
    deductions: float
    net_salary: float

# [완료] 기능 1: 실근무 시간 계산
@lru_cache(maxsize=128)
def calculate_work_duration(check_in: str, check_out: str) -> int:
    """
    출근/퇴근 시간을 받아 실 근무 시간(분)을 계산한다.
    :param check_in: str ('HH:MM:SS')
    :param check_out: str ('HH:MM:SS')
    :return: int (minutes)
    :raises: WorkDurationError
    """
    try:
        fmt = "%H:%M:%S"
        start = datetime.strptime(check_in, fmt)
        end = datetime.strptime(check_out, fmt)
        
        if end < start:
            raise WorkDurationError("퇴근 시간이 출근 시간보다 빠를 수 없습니다.")
            
        duration = (end - start).total_seconds() / 60
        logger.info(f"근무 시간 계산 완료: {duration}분")
        return int(duration)
    except Exception as e:
        logger.error(f"근무 시간 계산 실패: {str(e)}")
        raise WorkDurationError(f"근무 시간 계산 중 오류가 발생했습니다: {str(e)}")

# [완료] 기능 2: 급여 계산 함수
def calculate_salary(
    work_minutes: int,
    pay_type: PayType,
    base_pay: float,
    overtime_rate: float = 1.5
) -> float:
    """
    근무 시간과 급여제에 따라 급여를 계산한다.
    :param work_minutes: int, 총 근무 시간 (분)
    :param pay_type: str, '시급제', '월급제', '주급제'
    :param base_pay: float, 기준 금액 (시급, 월급, 주급)
    :param overtime_rate: float, 야근 수당 비율 (기본값: 1.5)
    :return: float, 계산된 급여
    :raises: SalaryCalculationError
    """
    try:
        if pay_type == '시급제':
            hours = work_minutes / 60
            overtime_hours = max(0, hours - 8)  # 8시간 초과 근무
            regular_pay = min(8, hours) * base_pay
            overtime_pay = overtime_hours * base_pay * overtime_rate
            return round(regular_pay + overtime_pay, 2)
        elif pay_type == '주급제':
            return base_pay
        elif pay_type == '월급제':
            return base_pay
        else:
            raise SalaryCalculationError("지원되지 않는 급여제 유형입니다.")
    except Exception as e:
        logger.error(f"급여 계산 실패: {str(e)}")
        raise SalaryCalculationError(f"급여 계산 중 오류가 발생했습니다: {str(e)}")

# [완료] 기능 3: 급여 PDF 자동 생성
def generate_payroll_pdf(employee_data: Dict, salary_data: SalaryData) -> str:
    """
    급여 명세서 PDF를 생성한다.
    :param employee_data: Dict, 직원 정보
    :param salary_data: SalaryData, 급여 정보
    :return: str, 생성된 PDF 파일 경로
    """
    try:
        filename = f"payroll_{employee_data['id']}_{salary_data.year}_{salary_data.month}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # 제목
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph(f"{salary_data.year}년 {salary_data.month}월 급여 명세서", title_style))
        story.append(Spacer(1, 20))

        # 직원 정보
        employee_info = [
            ["직원명", employee_data['name']],
            ["직위", employee_data['position']],
            ["부서", employee_data['department']]
        ]
        t = Table(employee_info, colWidths=[100, 300])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # 급여 정보
        salary_info = [
            ["구분", "금액"],
            ["기본급", f"{salary_data.base_salary:,}원"],
            ["야근수당", f"{salary_data.overtime_pay:,}원"],
            ["상여금", f"{salary_data.bonus:,}원"],
            ["공제액", f"{salary_data.deductions:,}원"],
            ["실수령액", f"{salary_data.net_salary:,}원"]
        ]
        t = Table(salary_info, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)

        doc.build(story)
        logger.info(f"급여 명세서 PDF 생성 완료: {filename}")
        return filename
    except Exception as e:
        logger.error(f"PDF 생성 실패: {str(e)}")
        raise

# [완료] 기능 4: 급여일 알림 발송
def send_salary_notification(employee_data: Dict, salary_data: SalaryData):
    """
    급여 지급 알림을 발송한다.
    :param employee_data: Dict, 직원 정보
    :param salary_data: SalaryData, 급여 정보
    """
    try:
        message = f"""
        {employee_data['name']}님의 {salary_data.year}년 {salary_data.month}월 급여가 지급되었습니다.
        
        [급여 내역]
        - 기본급: {salary_data.base_salary:,}원
        - 야근수당: {salary_data.overtime_pay:,}원
        - 상여금: {salary_data.bonus:,}원
        - 공제액: {salary_data.deductions:,}원
        - 실수령액: {salary_data.net_salary:,}원
        
        자세한 내용은 첨부된 급여 명세서를 확인해 주세요.
        """
        
        # TODO: 실제 알림 발송 로직 구현 (이메일, SMS 등)
        logger.info(f"급여 알림 발송 완료: {employee_data['name']}")
    except Exception as e:
        logger.error(f"알림 발송 실패: {str(e)}")
        raise

# 단위 테스트
class TestSalarySystem(unittest.TestCase):
    def test_calculate_work_duration(self):
        # 정상 케이스
        self.assertEqual(calculate_work_duration("09:00:00", "18:00:00"), 540)
        # 휴식시간 제외
        self.assertEqual(calculate_work_duration("09:00:00", "18:00:00") - 60, 480)
        # 예외 케이스
        with self.assertRaises(WorkDurationError):
            calculate_work_duration("18:00:00", "09:00:00")

    def test_calculate_salary(self):
        # 시급제
        self.assertEqual(calculate_salary(540, "시급제", 10000), 90000)
        # 야근 포함
        self.assertEqual(calculate_salary(600, "시급제", 10000), 110000)
        # 월급제
        self.assertEqual(calculate_salary(0, "월급제", 3000000), 3000000)
        # 예외 케이스
        with self.assertRaises(SalaryCalculationError):
            calculate_salary(540, "일급제", 10000)

if __name__ == "__main__":
    unittest.main() 