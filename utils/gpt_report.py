from datetime import date, timedelta
from models import SalesRecord, MenuItem, Ingredient, StockTransaction
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def analyze_sales_data(start_date, end_date):
    """
    판매 데이터를 분석하여 GPT로 요약 및 추천사항 생성
    
    Args:
        start_date (date): 시작일
        end_date (date): 종료일
    
    Returns:
        dict: 분석 결과 (요약, 추천사항, 인사이트)
    """
    # 판매 데이터 조회
    sales = SalesRecord.query.filter(
        SalesRecord.sold_at.between(start_date, end_date)
    ).all()
    
    # 메뉴별 판매 데이터 집계
    menu_sales = {}
    total_sales = 0
    total_quantity = 0
    
    for sale in sales:
        menu_name = sale.menu.name
        if menu_name not in menu_sales:
            menu_sales[menu_name] = {
                'quantity': 0,
                'total': 0
            }
        
        menu_sales[menu_name]['quantity'] += sale.quantity
        menu_sales[menu_name]['total'] += sale.total_price
        total_sales += sale.total_price
        total_quantity += sale.quantity
    
    # 재고 데이터 조회
    stock_alerts = StockTransaction.query.filter(
        StockTransaction.transaction_type == 'usage',
        StockTransaction.created_at.between(start_date, end_date)
    ).all()
    
    # GPT 프롬프트 생성
    prompt = f"""
    다음은 {start_date.strftime('%Y-%m-%d')}부터 {end_date.strftime('%Y-%m-%d')}까지의 판매 데이터입니다.
    
    총 판매액: {total_sales:,}원
    총 판매 수량: {total_quantity:,}개
    
    메뉴별 판매 현황:
    {chr(10).join([f'- {menu}: {data["quantity"]}개 ({data["total"]:,}원)' for menu, data in menu_sales.items()])}
    
    재고 사용 현황:
    {chr(10).join([f'- {alert.ingredient.name}: {alert.quantity} {alert.ingredient.unit}' for alert in stock_alerts])}
    
    위 데이터를 바탕으로 다음을 분석해주세요:
    1. 판매 현황 요약 (주요 트렌드, 특징)
    2. 개선이 필요한 부분
    3. 추천사항 (메뉴 개선, 재고 관리, 마케팅 등)
    
    각 항목별로 2-3개의 핵심 포인트를 제시해주세요.
    """
    
    try:
        # GPT API 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 레스토랑 경영 컨설턴트입니다. 판매 데이터를 분석하고 실질적인 개선 방안을 제시해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # 응답 파싱
        analysis = response.choices[0].message.content
        
        # 응답을 섹션별로 분리
        sections = analysis.split('\n\n')
        result = {
            'summary': sections[0] if len(sections) > 0 else '',
            'improvements': sections[1] if len(sections) > 1 else '',
            'recommendations': sections[2] if len(sections) > 2 else ''
        }
        
        return result
        
    except Exception as e:
        print(f"GPT 분석 중 오류 발생: {str(e)}")
        return {
            'summary': '데이터 분석 중 오류가 발생했습니다.',
            'improvements': '',
            'recommendations': ''
        } 