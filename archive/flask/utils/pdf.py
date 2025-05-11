from fpdf import FPDF
import os
from datetime import datetime
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from flask import current_app

logger = logging.getLogger(__name__)

def generate_store_report_pdf(content, filename='report'):
    """매장 보고서 PDF 생성"""
    try:
        # PDF 객체 생성
        pdf = FPDF()
        pdf.add_page()
        
        # 기본 폰트 설정
        pdf.set_font("Arial", size=12)
        
        # 제목 추가
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "매장 운영 보고서", ln=True, align='C')
        pdf.ln(10)
        
        # 날짜 추가
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(10)
        
        # 내용 추가
        pdf.set_font("Arial", size=12)
        for line in content.split("\n"):
            # 섹션 제목 처리
            if line.startswith("# "):
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, line[2:], ln=True)
                pdf.ln(5)
                pdf.set_font("Arial", size=12)
            else:
                pdf.multi_cell(0, 10, line)
        
        # 출력 디렉토리 생성
        output_dir = os.path.join('static', 'pdfs', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        filepath = os.path.join(output_dir, f"{filename}_{timestamp}.pdf")
        
        # PDF 저장
        pdf.output(filepath)
        
        logger.info(f"보고서 PDF 생성 완료: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"보고서 PDF 생성 중 오류 발생: {str(e)}")
        raise

def generate_contract_pdf(contract, employee):
    """계약서 PDF 생성"""
    try:
        # PDF 저장 경로 설정
        pdf_dir = os.path.join('static', 'contracts')
        os.makedirs(pdf_dir, exist_ok=True)
        
        filename = f"contract_{contract.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)
        
        # PDF 문서 생성
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12
        )
        normal_style = styles['Normal']
        
        # 문서 내용 구성
        story = []
        
        # 제목
        story.append(Paragraph("근로 계약서", title_style))
        story.append(Spacer(1, 12))
        
        # 근로자 정보
        story.append(Paragraph("1. 근로자 정보", heading_style))
        employee_data = [
            ["이름", employee.user.name],
            ["직책", employee.position],
            ["연락처", employee.user.phone],
            ["이메일", employee.user.email]
        ]
        employee_table = Table(employee_data, colWidths=[2*inch, 4*inch])
        employee_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(employee_table)
        story.append(Spacer(1, 20))
        
        # 계약 정보
        story.append(Paragraph("2. 계약 정보", heading_style))
        contract_data = [
            ["계약 기간", f"{contract.start_date.strftime('%Y-%m-%d')} ~ {contract.end_date.strftime('%Y-%m-%d')}"],
            ["급여 형태", contract.pay_type],
            ["급여", f"{contract.wage:,} 원"],
            ["서명일시", contract.signed_at.strftime('%Y-%m-%d %H:%M:%S') if contract.signed_at else "미서명"]
        ]
        contract_table = Table(contract_data, colWidths=[2*inch, 4*inch])
        contract_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(contract_table)
        story.append(Spacer(1, 20))
        
        # 근로 조건
        story.append(Paragraph("3. 근로 조건", heading_style))
        conditions = [
            "1. 근무 시간: 매일 9시간 (휴게시간 1시간 포함)",
            "2. 주휴일: 매주 일요일",
            "3. 연차: 근속 1년 미만 1개월 개근시 1일, 1년 이상 80% 출근시 15일",
            "4. 사회보험: 4대보험 가입"
        ]
        for condition in conditions:
            story.append(Paragraph(condition, normal_style))
        story.append(Spacer(1, 20))
        
        # 서명란
        story.append(Paragraph("4. 서명", heading_style))
        signature_data = [
            ["근로자", "사용자"],
            ["(서명)", "(서명)"],
            ["날짜: " + datetime.now().strftime('%Y-%m-%d'), "날짜: " + datetime.now().strftime('%Y-%m-%d')]
        ]
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(signature_table)
        
        # PDF 생성
        doc.build(story)
        
        logger.info(f"계약서 PDF 생성 완료: {pdf_path}")
        
        # 상대 경로 반환
        return os.path.join('contracts', filename)
        
    except Exception as e:
        logger.error(f"계약서 PDF 생성 중 오류 발생: {str(e)}")
        raise

def generate_evaluation_pdf(stats):
    """평가 보고서 PDF 생성
    
    Args:
        stats (dict): 평가 통계 데이터
        
    Returns:
        str: 생성된 PDF 파일 경로
    """
    # PDF 저장 폴더 생성
    folder = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(folder, exist_ok=True)
    
    # 파일명 생성
    filename = f'evaluation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    path = os.path.join(folder, filename)
    
    # PDF 생성
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    
    # 제목
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "근무 평가 보고서")
    
    # 통계 요약
    c.setFont("Helvetica", 12)
    y = height - 100
    c.drawString(50, y, f"총 평가 수: {stats['total_evaluations']}건")
    y -= 20
    c.drawString(50, y, f"평균 근무 강도: {stats['avg_intensity']}점")
    
    # 일별 평가 현황
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "일별 평가 현황")
    y -= 20
    c.setFont("Helvetica", 10)
    
    for eval_data in stats['daily_evaluations']:
        if y < 100:  # 페이지 끝에 도달하면 새 페이지
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
            
        c.drawString(50, y, f"날짜: {eval_data['date']}")
        y -= 15
        c.drawString(50, y, f"평가 수: {eval_data['count']}건")
        y -= 15
        c.drawString(50, y, f"평균 강도: {eval_data['avg_intensity']}점")
        y -= 25
    
    # 피드백 목록
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "피드백 목록")
    y -= 20
    c.setFont("Helvetica", 10)
    
    for feedback in stats['feedbacks']:
        if y < 100:  # 페이지 끝에 도달하면 새 페이지
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
            
        c.drawString(50, y, f"날짜: {feedback['date']}")
        y -= 15
        c.drawString(50, y, f"평가 점수: {feedback['intensity']}점")
        y -= 15
        c.drawString(50, y, f"피드백: {feedback['content']}")
        y -= 25
    
    # 강도별 분포
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "강도별 분포")
    y -= 20
    c.setFont("Helvetica", 10)
    
    for score, count in stats['intensity_distribution'].items():
        if y < 100:  # 페이지 끝에 도달하면 새 페이지
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
            
        c.drawString(50, y, f"{score}점: {count}건")
        y -= 20
    
    c.save()
    return path 

def generate_termination_pdf(document, output_path):
    """퇴직/해고/계약해지 문서 PDF 생성"""
    try:
        # PDF 생성
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12
        )
        
        # 문서 내용
        story = []
        
        # 제목
        if document.document_type == 'resignation':
            title = "퇴직서"
        elif document.document_type == 'dismissal':
            title = "해고 통지서"
        else:
            title = "계약 해지 계약서"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # 기본 정보
        story.append(Paragraph("1. 당사자 정보", heading_style))
        employee_data = [
            ["이름", document.employee.user.name],
            ["직위", document.employee.position],
            ["생년월일", document.employee.user.birth_date.strftime('%Y-%m-%d')],
            ["주소", document.employee.user.address],
            ["연락처", document.employee.user.phone]
        ]
        employee_table = Table(employee_data, colWidths=[2*inch, 4*inch])
        employee_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(employee_table)
        story.append(Spacer(1, 20))
        
        # 문서 정보
        story.append(Paragraph("2. 문서 정보", heading_style))
        doc_data = [
            ["문서 종류", title],
            ["효력 발생일", document.effective_date.strftime('%Y년 %m월 %d일')],
            ["작성일", document.created_at.strftime('%Y년 %m월 %d일')]
        ]
        doc_table = Table(doc_data, colWidths=[2*inch, 4*inch])
        doc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(doc_table)
        story.append(Spacer(1, 20))
        
        # 사유
        story.append(Paragraph("3. 사유", heading_style))
        story.append(Paragraph(document.reason, normal_style))
        story.append(Spacer(1, 20))
        
        # 법적 고지
        story.append(Paragraph("4. 법적 고지", heading_style))
        legal_notice = """
        본 문서는 근로기준법 및 관련 법령에 따라 작성되었으며, 당사자 간의 합의에 의한 것입니다.
        본 문서의 효력은 서명이 완료된 시점부터 발생하며, 법적 구속력을 가집니다.
        """
        story.append(Paragraph(legal_notice, normal_style))
        story.append(Spacer(1, 20))
        
        # 서명란
        story.append(Paragraph("5. 서명", heading_style))
        signature_data = [
            ["직원", "관리자"],
            ["(서명)", "(서명)"],
            [
                f"날짜: {document.employee_signed_at.strftime('%Y-%m-%d %H:%M')}" if document.employee_signed_at else "날짜: _________________",
                f"날짜: {document.admin_signed_at.strftime('%Y-%m-%d %H:%M')}" if document.admin_signed_at else "날짜: _________________"
            ]
        ]
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(signature_table)
        
        # PDF 생성
        doc.build(story)
        return True
        
    except Exception as e:
        logger.error(f"PDF 생성 중 오류 발생: {str(e)}")
        return False 

def generate_payroll_pdf(employee, wage_info, year, month):
    """급여 명세서 PDF 생성
    
    Args:
        employee (Employee): 직원 정보
        wage_info (dict): 급여 정보
        year (int): 연도
        month (int): 월
        
    Returns:
        str: 생성된 PDF 파일 경로
    """
    try:
        # PDF 저장 폴더 생성
        folder = os.path.join(current_app.root_path, 'static', 'payrolls')
        os.makedirs(folder, exist_ok=True)
        
        # 파일명 생성
        filename = f'payroll_{employee.id}_{year}{month:02d}.pdf'
        path = os.path.join(folder, filename)
        
        # PDF 생성
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12
        )
        normal_style = styles['Normal']
        
        # 문서 내용 구성
        story = []
        
        # 제목
        story.append(Paragraph(f"{year}년 {month}월 급여 명세서", title_style))
        story.append(Spacer(1, 12))
        
        # 직원 정보
        story.append(Paragraph("1. 직원 정보", heading_style))
        employee_data = [
            ["이름", employee.user.name],
            ["직책", employee.position],
            ["사번", str(employee.id)]
        ]
        employee_table = Table(employee_data, colWidths=[2*inch, 4*inch])
        employee_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(employee_table)
        story.append(Spacer(1, 20))
        
        # 급여 정보
        story.append(Paragraph("2. 급여 정보", heading_style))
        wage_data = [
            ["기본급", f"{wage_info['base_wage']:,} 원"],
            ["초과근무수당", f"{wage_info['overtime_pay']:,} 원"],
            ["휴일근무수당", f"{wage_info['holiday_pay']:,} 원"],
            ["총 급여", f"{wage_info['total_wage']:,} 원"]
        ]
        wage_table = Table(wage_data, colWidths=[2*inch, 4*inch])
        wage_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(wage_table)
        story.append(Spacer(1, 20))
        
        # 근무 정보
        story.append(Paragraph("3. 근무 정보", heading_style))
        work_data = [
            ["정상근무시간", f"{wage_info['regular_hours']} 시간"],
            ["초과근무시간", f"{wage_info['overtime_hours']} 시간"],
            ["휴일근무시간", f"{wage_info['holiday_hours']} 시간"],
            ["총 근무시간", f"{wage_info['total_hours']} 시간"]
        ]
        work_table = Table(work_data, colWidths=[2*inch, 4*inch])
        work_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(work_table)
        
        # PDF 생성
        doc.build(story)
        
        logger.info(f"급여 명세서 PDF 생성 완료: {path}")
        
        # 상대 경로 반환
        return os.path.join('payrolls', filename)
        
    except Exception as e:
        logger.error(f"급여 명세서 PDF 생성 중 오류 발생: {str(e)}")
        raise 