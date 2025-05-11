from datetime import datetime, date, timedelta
from models import Ingredient, OrderItem, StockTransaction
from sqlalchemy import func, and_

def get_monthly_inventory_report(year, month):
    """
    해당 연월의 재고 현황 리포트 생성
    
    Returns:
        tuple: (report_data, start_date, end_date)
    """
    # 날짜 범위 설정
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
        
    # 모든 식자재 조회
    ingredients = Ingredient.query.all()
    report_data = {}
    
    for ingredient in ingredients:
        # 발주량 집계
        ordered = OrderItem.query.filter(
            and_(
                OrderItem.ingredient_id == ingredient.id,
                OrderItem.created_at >= start_date,
                OrderItem.created_at <= end_date
            )
        ).with_entities(
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.total_cost).label('total_cost')
        ).first()
        
        # 입고량 집계
        received = StockTransaction.query.filter(
            and_(
                StockTransaction.ingredient_id == ingredient.id,
                StockTransaction.transaction_type == 'purchase',
                StockTransaction.created_at >= start_date,
                StockTransaction.created_at <= end_date
            )
        ).with_entities(
            func.sum(StockTransaction.quantity).label('total_quantity')
        ).first()
        
        # 사용량 집계
        used = StockTransaction.query.filter(
            and_(
                StockTransaction.ingredient_id == ingredient.id,
                StockTransaction.transaction_type == 'usage',
                StockTransaction.created_at >= start_date,
                StockTransaction.created_at <= end_date
            )
        ).with_entities(
            func.sum(StockTransaction.quantity).label('total_quantity')
        ).first()
        
        # 리포트 데이터 구성
        report_data[ingredient.name] = {
            'current_stock': ingredient.current_stock,
            'min_stock': ingredient.min_stock,
            'unit': ingredient.unit,
            'ordered_quantity': float(ordered.total_quantity or 0),
            'ordered_cost': float(ordered.total_cost or 0),
            'received_quantity': float(received.total_quantity or 0),
            'used_quantity': abs(float(used.total_quantity or 0)),
            'cost_per_unit': ingredient.cost_per_unit
        }
        
    return report_data, start_date, end_date 