from extensions import db
from datetime import datetime, timedelta
from models.contract import Contract
from models.attendance import Attendance
from fpdf import FPDF
import json
import os
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class Employee(Base):
    """직원 모델"""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(20))
    position = Column(String(50))
    hire_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scheduled_check_in = Column(String(8), default='09:00:00')  # 기본 출근 시간
    pay_type = Column(String(20), default='시급제')  # 시급제, 주급제, 월급제
    base_pay = Column(Float, default=0.0)  # 기본 급여

    # 관계
    user = relationship('User', back_populates='employee')
    contracts = relationship('Contract', back_populates='employee')
    attendances = relationship('Attendance', back_populates='employee')
    schedules = relationship('Schedule', back_populates='employee')
    payrolls = relationship('Payroll', back_populates='employee')
    evaluations = relationship('WorkEvaluation', back_populates='employee')

    def calculate_work_duration(self, check_in, check_out):
        """근무 시간과 지각 여부를 계산합니다."""
        if isinstance(check_in, str):
            check_in = datetime.strptime(check_in, "%H:%M:%S").time()
        if isinstance(check_out, str):
            check_out = datetime.strptime(check_out, "%H:%M:%S").time()
        
        start = datetime.combine(datetime.today(), check_in)
        end = datetime.combine(datetime.today(), check_out)
        standard = datetime.combine(datetime.today(), self.scheduled_check_in)
        
        duration = (end - start).total_seconds() / 60
        late = start > standard
        
        return int(duration), late

    def calculate_salary(self, work_minutes):
        """급여를 계산합니다."""
        if self.pay_type == '시급제':
            hours = work_minutes / 60
            return round(hours * self.base_pay, 2)
        elif self.pay_type == '주급제':
            return self.base_pay
        elif self.pay_type == '월급제':
            return self.base_pay
        else:
            raise ValueError("지원되지 않는 급여제 유형입니다.")

    def generate_payroll_pdf(self, work_minutes, salary, payday, late=False):
        """급여 명세서 PDF를 생성합니다."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_fill_color(240, 240, 240)
        
        # 제목
        pdf.cell(200, 10, txt=f"💼 급여 명세서", ln=True, align='C')
        pdf.ln(10)
        
        # 직원 정보
        pdf.cell(200, 10, txt=f"직원명: {self.name}", ln=True)
        pdf.cell(200, 10, txt=f"직위: {self.position}", ln=True)
        pdf.cell(200, 10, txt=f"총 근무 시간: {work_minutes}분", ln=True)
        pdf.cell(200, 10, txt=f"지각 여부: {'예' if late else '아니오'}", ln=True)
        pdf.cell(200, 10, txt=f"지급 급여: {salary:,}원", ln=True)
        pdf.cell(200, 10, txt=f"지급일: {payday}", ln=True)
        
        # 파일 저장
        os.makedirs("static/payrolls", exist_ok=True)
        filename = f"payroll_{self.name}_{payday}.pdf"
        filepath = os.path.join("static/payrolls", filename)
        pdf.output(filepath)
        return filename

    def record_work_evaluation(self, score, comment):
        """근무 평가를 기록합니다."""
        evaluation = WorkEvaluation(
            employee_id=self.id,
            evaluator_id=None,  # 익명 평가
            evaluation_date=datetime.now().date(),
            performance_score=score,
            comments=comment
        )
        db.session.add(evaluation)
        db.session.commit()
        
        # JSON 파일로도 저장
        os.makedirs("data/evaluation", exist_ok=True)
        data = {
            "employee_id": self.id,
            "employee_name": self.name,
            "score": score,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        filename = f"data/evaluation/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def generate_evaluation_report(self):
        """근무 평가 리포트를 생성합니다."""
        evaluations = WorkEvaluation.query.filter_by(employee_id=self.id).all()
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # 제목
        pdf.cell(200, 10, txt="📊 근무 평가 리포트", ln=True, align='C')
        pdf.ln(10)
        
        # 직원 정보
        pdf.cell(200, 10, txt=f"직원명: {self.name}", ln=True)
        pdf.cell(200, 10, txt=f"직위: {self.position}", ln=True)
        pdf.ln(10)
        
        # 평가 목록
        for eval in evaluations:
            pdf.cell(200, 10, txt=f"평가일: {eval.evaluation_date}", ln=True)
            pdf.cell(200, 10, txt=f"점수: {eval.performance_score}점", ln=True)
            pdf.cell(200, 10, txt=f"의견: {eval.comments}", ln=True)
            pdf.ln(5)
        
        # 파일 저장
        os.makedirs("static/evaluations", exist_ok=True)
        filename = f"evaluation_report_{self.name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join("static/evaluations", filename)
        pdf.output(filepath)
        return filename
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.name})>"

class Payroll(db.Model):
    """급여 모델"""
    __tablename__ = 'payrolls'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    total_work_minutes = Column(Integer, default=0)  # 총 근무 시간(분)
    base_salary = Column(Float, nullable=False)  # 기본급
    overtime_pay = Column(Float, default=0.0)  # 야근수당
    bonus = Column(Float, default=0.0)  # 상여금
    deductions = Column(Float, default=0.0)  # 공제액
    net_salary = Column(Float, nullable=False)  # 실수령액
    payment_date = Column(DateTime)  # 지급일
    payment_status = Column(String(20), default='pending')  # pending, paid
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    employee = relationship('Employee', back_populates='payrolls')
    
    def __repr__(self):
        return f'<Payroll {self.employee_id} - {self.year}/{self.month}>'
    
    def calculate_total_salary(self):
        """총 급여 계산"""
        return self.base_salary + self.overtime_pay + self.bonus - self.deductions

class WorkEvaluation(db.Model):
    """근무 평가 모델"""
    __tablename__ = 'work_evaluations'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    evaluator_id = Column(Integer, ForeignKey('users.id'))  # 익명 평가의 경우 NULL
    evaluation_date = Column(DateTime, nullable=False)
    performance_score = Column(Integer, nullable=False)  # 1-5점
    comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    employee = relationship('Employee', back_populates='evaluations')
    evaluator = relationship('User', back_populates='evaluations')
    
    def __repr__(self):
        return f'<WorkEvaluation {self.employee_id} - {self.evaluation_date}>'

class TerminationDocument(db.Model):
    """퇴사 문서 모델"""
    __tablename__ = 'termination_documents'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    termination_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    notice_period = Column(Integer)  # 통지 기간(일)
    final_settlement = Column(Float)  # 최종 정산금
    approved_by = Column(Integer, ForeignKey('users.id'))
    approval_date = Column(DateTime)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    employee = relationship('Employee', backref=relationship('termination_documents', lazy=True))
    approver = relationship('User', backref=relationship('approved_terminations', lazy=True))
    
    def __repr__(self):
        return f'<TerminationDocument {self.employee_id} - {self.termination_date}>'
