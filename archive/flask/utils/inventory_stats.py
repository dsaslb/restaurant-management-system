from models import StockTransaction, Ingredient
from sqlalchemy import func
from datetime import datetime, timedelta

def get_usage_statistics(start_date=None, end_date=None):
    """재고 사용 통계 데이터 조회"""
    try:
        # 기본 쿼리
        query = StockTransaction.query.filter_by(transaction_type='usage')
        
        # 날짜 필터 적용
        if start_date:
            query = query.filter(StockTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(StockTransaction.created_at <= end_date)
            
        # 전체 사용량 통계
        total_usage = query.with_entities(
            func.sum(StockTransaction.quantity).label('total_quantity')
        ).scalar() or 0
        
        # 식자재별 사용량
        ingredient_usage = query.with_entities(
            StockTransaction.ingredient_id,
            Ingredient.name,
            Ingredient.unit,
            func.sum(StockTransaction.quantity).label('total_quantity')
        ).join(Ingredient).group_by(
            StockTransaction.ingredient_id,
            Ingredient.name,
            Ingredient.unit
        ).all()
        
        # 일별 사용량 추이
        daily_usage = query.with_entities(
            func.date(StockTransaction.created_at).label('date'),
            func.sum(StockTransaction.quantity).label('total_quantity')
        ).group_by(
            func.date(StockTransaction.created_at)
        ).order_by(
            func.date(StockTransaction.created_at)
        ).all()
        
        # 사용자별 사용량
        user_usage = query.with_entities(
            StockTransaction.created_by,
            func.sum(StockTransaction.quantity).label('total_quantity')
        ).group_by(
            StockTransaction.created_by
        ).all()
        
        return {
            'total_usage': abs(total_usage),
            'ingredient_usage': [
                {
                    'ingredient_id': ing_id,
                    'name': name,
                    'unit': unit,
                    'quantity': abs(qty)
                }
                for ing_id, name, unit, qty in ingredient_usage
            ],
            'daily_usage': [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'quantity': abs(qty)
                }
                for date, qty in daily_usage
            ],
            'user_usage': [
                {
                    'user_id': user_id,
                    'quantity': abs(qty)
                }
                for user_id, qty in user_usage
            ]
        }
        
    except Exception as e:
        print(f"통계 데이터 조회 중 오류 발생: {str(e)}")
        return None 