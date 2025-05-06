from datetime import datetime
from models import db, StockItem, StockTransaction, Notification, User

def consume_stock(ingredient_id: int, quantity: float, user_id: int, notes: str = None):
    """
    재고에서 quantity만큼 차감합니다.
    재고가 부족하면 ValueError를 발생시킵니다.
    
    Args:
        ingredient_id (int): 식자재 ID
        quantity (float): 차감할 수량
        user_id (int): 사용자 ID
        notes (str, optional): 메모
    
    Returns:
        StockTransaction: 생성된 거래 내역
    
    Raises:
        ValueError: 재고가 부족한 경우
    """
    stock = StockItem.query.filter_by(ingredient_id=ingredient_id).first()
    if not stock or stock.quantity < quantity:
        raise ValueError("재고가 부족합니다.")

    # 재고 차감
    stock.quantity -= quantity
    stock.updated_at = datetime.utcnow()
    
    # 거래 내역 생성
    transaction = StockTransaction(
        ingredient_id=ingredient_id,
        transaction_type='usage',
        quantity=quantity,
        created_by=user_id,
        notes=notes
    )
    db.session.add(transaction)
    
    # 재고 부족 알림
    if stock.quantity <= stock.ingredient.min_stock:
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                title='재고 부족 알림',
                message=f"{stock.ingredient.name}의 재고가 부족합니다. (현재: {stock.quantity} {stock.ingredient.unit})"
            )
            db.session.add(notification)
    
    db.session.commit()
    return transaction 