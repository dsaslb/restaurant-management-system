import openai
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from models.inventory import Inventory, Order, ProductCategory
from database import db

logger = logging.getLogger(__name__)

class GPTAnalyzer:
    """GPT를 활용한 재고 및 발주 분석 클래스"""
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key (str): OpenAI API 키
        """
        openai.api_key = api_key
    
    def analyze_inventory_trends(self, days: int = 30) -> Dict:
        """
        재고 트렌드를 분석합니다.
        
        Args:
            days (int): 분석 기간 (일)
            
        Returns:
            Dict: 분석 결과
        """
        try:
            # 재고 데이터 수집
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            inventory_data = []
            for category in ProductCategory:
                items = Inventory.query.filter_by(category=category).all()
                for item in items:
                    inventory_data.append({
                        'name': item.name,
                        'category': category.value,
                        'quantity': item.quantity,
                        'status': item.status.value,
                        'orders': len(item.orders)
                    })
            
            # GPT 분석 요청
            prompt = f"""
            다음은 {days}일간의 재고 데이터입니다. 다음 항목들을 분석해주세요:
            1. 카테고리별 재고 현황
            2. 부족 재고 항목
            3. 발주 빈도가 높은 항목
            4. 개선 제안
            
            데이터: {inventory_data}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 재고 관리 전문가입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                'analysis': response.choices[0].message.content,
                'data': inventory_data
            }
            
        except Exception as e:
            logger.error(f"재고 트렌드 분석 중 오류 발생: {str(e)}")
            raise
    
    def predict_order_quantity(self, inventory_id: int) -> Dict:
        """
        발주 수량을 예측합니다.
        
        Args:
            inventory_id (int): 재고 ID
            
        Returns:
            Dict: 예측 결과
        """
        try:
            # 재고 정보 조회
            inventory = Inventory.query.get_or_404(inventory_id)
            
            # 과거 발주 데이터 수집
            orders = Order.query.filter_by(inventory_id=inventory_id).all()
            order_history = [{
                'date': order.order_date.strftime('%Y-%m-%d'),
                'quantity': order.quantity,
                'status': order.status
            } for order in orders]
            
            # GPT 예측 요청
            prompt = f"""
            다음은 {inventory.name}의 과거 발주 데이터입니다. 
            다음 발주 시 적정 수량을 예측해주세요.
            
            현재 재고: {inventory.quantity}{inventory.unit}
            발주 이력: {order_history}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 발주 관리 전문가입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                'prediction': response.choices[0].message.content,
                'history': order_history
            }
            
        except Exception as e:
            logger.error(f"발주 수량 예측 중 오류 발생: {str(e)}")
            raise
    
    def analyze_supplier_performance(self) -> Dict:
        """
        공급업체 성과를 분석합니다.
        
        Returns:
            Dict: 분석 결과
        """
        try:
            # 공급업체 데이터 수집
            suppliers = {}
            orders = Order.query.all()
            
            for order in orders:
                supplier = order.inventory.supplier
                if supplier:
                    if supplier not in suppliers:
                        suppliers[supplier] = {
                            'total_orders': 0,
                            'total_amount': 0,
                            'on_time_delivery': 0,
                            'late_delivery': 0
                        }
                    
                    suppliers[supplier]['total_orders'] += 1
                    suppliers[supplier]['total_amount'] += order.quantity * order.inventory.price
                    
                    if order.status == '입고완료':
                        if order.delivery_date >= order.order_date:
                            suppliers[supplier]['on_time_delivery'] += 1
                        else:
                            suppliers[supplier]['late_delivery'] += 1
            
            # GPT 분석 요청
            prompt = f"""
            다음은 공급업체별 성과 데이터입니다. 각 업체의 성과를 분석하고 개선점을 제시해주세요.
            
            데이터: {suppliers}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 공급업체 관리 전문가입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                'analysis': response.choices[0].message.content,
                'data': suppliers
            }
            
        except Exception as e:
            logger.error(f"공급업체 성과 분석 중 오류 발생: {str(e)}")
            raise 