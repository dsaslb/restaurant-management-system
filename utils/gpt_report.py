from datetime import date, timedelta
from models import SalesRecord, MenuItem, Ingredient, StockTransaction
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any

load_dotenv()

logger = logging.getLogger(__name__)

def _is_openai_api_key_valid() -> bool:
    """
    OpenAI API 키의 유효성을 검사합니다.
    
    Returns:
        bool: API 키가 유효한지 여부
    """
    api_key = os.getenv('OPENAI_API_KEY')
    return bool(api_key and api_key.strip())

def analyze_sales_data(start_date, end_date):
    """
    판매 데이터를 분석하여 GPT로 요약 및 추천사항 생성
    
    Args:
        start_date (date): 시작일
        end_date (date): 종료일
    
    Returns:
        dict: 분석 결과 (요약, 추천사항, 인사이트)
    """
    if not _is_openai_api_key_valid():
        logger.warning("OpenAI API 키가 설정되지 않아 데이터 분석을 건너뜁니다.")
        return {
            'summary': '데이터 분석을 위한 OpenAI API 키가 설정되지 않았습니다.',
            'improvements': '',
            'recommendations': ''
        }

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
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
        logger.error(f"GPT 분석 중 오류 발생: {str(e)}")
        return {
            'summary': '데이터 분석 중 오류가 발생했습니다.',
            'improvements': '',
            'recommendations': ''
        }

def generate_report(data: Dict[str, Any]) -> Optional[str]:
    """
    GPT를 사용하여 보고서를 생성합니다.
    
    Args:
        data (Dict[str, Any]): 보고서 생성에 필요한 데이터
        
    Returns:
        Optional[str]: 생성된 보고서
    """
    if not _is_openai_api_key_valid():
        logger.warning("OpenAI API 키가 설정되지 않아 보고서 생성을 건너뜁니다.")
        return None

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # 보고서 생성 로직
        return "GPT로 생성된 보고서 내용"
        
    except Exception as e:
        logger.error(f"GPT 보고서 생성 중 오류 발생: {str(e)}")
        return None 