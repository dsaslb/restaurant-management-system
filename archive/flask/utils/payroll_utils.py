from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import json

def calculate_work_duration(check_in: str, check_out: str, scheduled_check_in: str = "09:00:00") -> tuple[int, bool]:
    """출퇴근 시간 비교 및 지각 여부 판별"""
    fmt = "%H:%M:%S"
    start = datetime.strptime(check_in, fmt)
    end = datetime.strptime(check_out, fmt)
    standard = datetime.strptime(scheduled_check_in, fmt)
    duration = (end - start).total_seconds() / 60
    late = start > standard
    return int(duration), late

def calculate_salary(work_minutes: int, pay_type: str, base_pay: float) -> float:
    """급여 계산 함수 (시급제/월급제/주급제)"""
    if pay_type == '시급제':
        hours = work_minutes / 60
        return round(hours * base_pay, 2)
    elif pay_type == '주급제':
        return base_pay
    elif pay_type == '월급제':
        return base_pay
    else:
        raise ValueError("지원되지 않는 급여제 유형입니다.")

def generate_payroll_pdf(username: str, work_minutes: int, salary: float, payday: str, late: bool = False) -> str:
    """급여 PDF 생성 함수"""
    os.makedirs("payroll", exist_ok=True)
    filename = f"payroll/payroll_{username}_{payday}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # 제목
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 50, "급여 명세서")
    
    # 내용
    y = height - 100
    c.setFont("Helvetica", 12)
    c.drawString(100, y, f"직원명: {username}")
    y -= 25
    c.drawString(100, y, f"총 근무 시간: {work_minutes}분")
    y -= 25
    c.drawString(100, y, f"지각 여부: {'예' if late else '아니오'}")
    y -= 25
    c.drawString(100, y, f"지급 급여: {salary:,.0f}원")
    y -= 25
    c.drawString(100, y, f"지급일: {payday}")
    
    c.save()
    return filename

def record_work_evaluation(score: int, comment: str) -> str:
    """익명 근무 평가 저장"""
    data = {
        "score": score,
        "comment": comment,
        "timestamp": datetime.now().isoformat()
    }
    os.makedirs("data/evaluation", exist_ok=True)
    filename = f"data/evaluation/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return filename

def generate_evaluation_report() -> str:
    """평가 PDF 리포트 생성"""
    folder = "data/evaluation"
    os.makedirs(folder, exist_ok=True)
    evaluations = []
    
    for file in os.listdir(folder):
        if file.endswith(".json"):
            with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                evaluations.append(json.load(f))
    
    filename = f"data/evaluation_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # 제목
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, "근무 평가 리포트")
    
    # 내용
    y = height - 100
    c.setFont("Helvetica", 12)
    for e in evaluations:
        c.drawString(100, y, f"점수: {e['score']}점  |  의견: {e['comment']}")
        y -= 20
        if y < 100:  # 페이지 끝에 도달하면 새 페이지
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 12)
    
    c.save()
    return filename 