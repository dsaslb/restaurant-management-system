from datetime import date, timedelta
from models import SalesRecord, Ingredient, StockTransaction
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

def generate_sales_report(year, month, frequency='monthly'):
    """
    판매 보고서 PDF 생성
    
    Args:
        year (int): 연도
        month (int): 월
        frequency (str): 'monthly' 또는 'weekly'
    
    Returns:
        str: 생성된 PDF 파일 경로
    """
    # 날짜 범위 계산
    if frequency == 'monthly':
        start = date(year, month, 1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    else:
        end = date.today()
        start = end - timedelta(days=7)
    
    # 데이터 조회
    sales = SalesRecord.query.filter(
        SalesRecord.sold_at.between(start, end)
    ).all()
    
    # PDF 생성
    folder = os.path.join('reports')
    os.makedirs(folder, exist_ok=True)
    filename = f"sales_report_{frequency}_{year}_{month if frequency=='monthly' else 'week'}.pdf"
    path = os.path.join(folder, filename)
    
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # 제목
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph(
        f"판매 보고서 ({frequency.capitalize()})",
        title_style
    ))
    
    # 기간
    elements.append(Paragraph(
        f"기간: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}",
        styles['Normal']
    ))
    
    # 판매 요약
    total_sales = sum(s.total_price for s in sales)
    total_quantity = sum(s.quantity for s in sales)
    
    summary_data = [
        ['총 판매액', f"{total_sales:,}원"],
        ['총 판매 수량', f"{total_quantity:,}개"],
        ['평균 판매액', f"{total_sales/len(sales):,.0f}원" if sales else "0원"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    
    # 메뉴별 판매 현황
    elements.append(Paragraph("메뉴별 판매 현황", styles['Heading2']))
    
    menu_data = [['메뉴', '수량', '판매액', '비중']]
    for sale in sales:
        menu_data.append([
            sale.menu.name,
            f"{sale.quantity:,}개",
            f"{sale.total_price:,}원",
            f"{(sale.total_price/total_sales*100):.1f}%" if total_sales > 0 else "0%"
        ])
    
    menu_table = Table(menu_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
    menu_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(menu_table)
    
    # PDF 생성
    doc.build(elements)
    return path 