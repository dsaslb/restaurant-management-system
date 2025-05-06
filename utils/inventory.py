from datetime import datetime
from models import db, StockItem, StockTransaction, Notification, User
from models.inventory import InventoryItem, InventoryBatch
from extensions import db
from datetime import date
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

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

def check_inventory_availability(item_name: str, quantity_needed: int) -> Tuple[bool, Optional[str]]:
    """
    재고 가용성 확인
    
    Returns:
        Tuple[bool, Optional[str]]: (가용 여부, 오류 메시지)
    """
    item = InventoryItem.query.filter_by(name=item_name).first()
    if not item:
        return False, f"품목 '{item_name}'을(를) 찾을 수 없습니다."
    
    if quantity_needed <= 0:
        return False, "필요 수량은 0보다 커야 합니다."
    
    total_available = sum(batch.available_quantity for batch in item.batches)
    if total_available < quantity_needed:
        return False, f"재고 부족: 필요 수량 {quantity_needed}{item.unit}, 가용 수량 {total_available}{item.unit}"
    
    return True, None

def consume_inventory(item_name: str, quantity_needed: int, reason: str = None) -> Tuple[bool, Optional[str]]:
    """
    유통기한 순으로 출고 재고 차감
    
    Args:
        item_name (str): 품목명
        quantity_needed (int): 필요 수량
        reason (str, optional): 출고 사유
    
    Returns:
        Tuple[bool, Optional[str]]: (성공 여부, 오류 메시지)
    """
    # 재고 가용성 확인
    is_available, error_msg = check_inventory_availability(item_name, quantity_needed)
    if not is_available:
        return False, error_msg

    try:
        item = InventoryItem.query.filter_by(name=item_name).first()
        batches = InventoryBatch.query.filter_by(item_id=item.id)\
            .filter(InventoryBatch.expiration_date >= date.today())\
            .order_by(InventoryBatch.expiration_date).all()

        remaining = quantity_needed
        for batch in batches:
            if remaining <= 0:
                break
                
            available = batch.available_quantity
            if available == 0:
                continue
                
            if available >= remaining:
                batch.used_quantity += remaining
                remaining = 0
            else:
                batch.used_quantity += available
                remaining -= available

        # 현재 재고 수량 업데이트
        item.update_current_quantity()
        
        # 로그 기록
        logger.info(f"재고 출고: {item_name} {quantity_needed}{item.unit} (사유: {reason or '미지정'})")
        
        db.session.commit()
        return True, None
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"재고 출고 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def get_inventory_status(item_name: str) -> dict:
    """
    특정 품목의 재고 상태 조회
    
    Returns:
        dict: 재고 상태 정보
    """
    item = InventoryItem.query.filter_by(name=item_name).first()
    if not item:
        return {"error": f"품목 '{item_name}'을(를) 찾을 수 없습니다."}
    
    batches = InventoryBatch.query.filter_by(item_id=item.id)\
        .order_by(InventoryBatch.expiration_date).all()
    
    total_available = sum(batch.available_quantity for batch in batches)
    expiring_soon = [batch for batch in batches 
                    if batch.available_quantity > 0 and batch.days_until_expiration <= 7]
    
    return {
        "item_name": item.name,
        "unit": item.unit,
        "total_available": total_available,
        "min_quantity": item.min_quantity,
        "is_low_stock": total_available <= item.min_quantity,
        "expiring_soon": [{
            "batch_number": batch.batch_number,
            "quantity": batch.available_quantity,
            "days_until_expiration": batch.days_until_expiration
        } for batch in expiring_soon]
    } 

def register_inventory(item_name: str, quantity: int, expiration_date: date, 
                      supplier: str = None, purchase_price: float = None) -> Tuple[bool, Optional[str]]:
    """
    새로운 재고 배치 등록
    
    Args:
        item_name (str): 품목명
        quantity (int): 수량
        expiration_date (date): 유통기한
        supplier (str, optional): 공급업체
        purchase_price (float, optional): 구매 가격
    
    Returns:
        Tuple[bool, Optional[str]]: (성공 여부, 오류 메시지)
    """
    try:
        # 품목 존재 확인
        item = InventoryItem.query.filter_by(name=item_name).first()
        if not item:
            return False, f"품목 '{item_name}'을(를) 찾을 수 없습니다."
        
        # 유효성 검사
        if quantity <= 0:
            return False, "수량은 0보다 커야 합니다."
        
        if expiration_date <= date.today():
            return False, "유통기한은 오늘 이후여야 합니다."
        
        # 배치 번호 생성 (YYYYMMDD-품목ID-순번)
        today = date.today()
        batch_count = InventoryBatch.query.filter(
            InventoryBatch.item_id == item.id,
            db.func.date(InventoryBatch.created_at) == today
        ).count()
        
        batch_number = f"{today.strftime('%Y%m%d')}-{item.id:03d}-{batch_count + 1:03d}"
        
        # 새 배치 생성
        new_batch = InventoryBatch(
            item_id=item.id,
            batch_number=batch_number,
            quantity=quantity,
            expiration_date=expiration_date,
            supplier=supplier,
            purchase_price=purchase_price
        )
        
        db.session.add(new_batch)
        
        # 현재 재고 수량 업데이트
        item.update_current_quantity()
        
        # 로그 기록
        logger.info(
            f"재고 입고: {item_name} {quantity}{item.unit} "
            f"(배치: {batch_number}, 유통기한: {expiration_date}, "
            f"공급업체: {supplier or '미지정'})"
        )
        
        # 재고 부족 알림 해제 (필요한 경우)
        if item.current_quantity > item.min_quantity:
            # TODO: 재고 부족 알림 해제 로직 구현
            pass
        
        db.session.commit()
        return True, None
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"재고 등록 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def get_inventory_batch(batch_number: str) -> Optional[dict]:
    """
    특정 배치의 상세 정보 조회
    
    Args:
        batch_number (str): 배치 번호
    
    Returns:
        Optional[dict]: 배치 정보 또는 None
    """
    batch = InventoryBatch.query.filter_by(batch_number=batch_number).first()
    if not batch:
        return None
    
    return {
        "batch_number": batch.batch_number,
        "item_name": batch.item.name,
        "quantity": batch.quantity,
        "used_quantity": batch.used_quantity,
        "available_quantity": batch.available_quantity,
        "received_date": batch.received_date,
        "expiration_date": batch.expiration_date,
        "days_until_expiration": batch.days_until_expiration,
        "supplier": batch.supplier,
        "purchase_price": batch.purchase_price,
        "created_at": batch.created_at
    } 