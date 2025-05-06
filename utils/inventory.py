from datetime import datetime, date, timedelta
from typing import Tuple, Optional
import logging
import requests
import json
from models import (
    db, Inventory, Order, StockItem, StockTransaction, User, 
    InventoryItem, InventoryBatch, StockUsageAlert, Notification
)
from utils.notification import send_notification
from config import Config
from extensions import db

logger = logging.getLogger(__name__)

def sync_pos_inventory():
    """
    POS 시스템에서 실시간 재고 정보를 동기화
    """
    try:
        # POS API 호출
        headers = {
            'Authorization': f'Bearer {Config.POS_API_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f'{Config.POS_API_URL}/inventory', headers=headers)
        response.raise_for_status()
        
        pos_data = response.json()
        
        # 재고 정보 업데이트
        for item_data in pos_data['items']:
            item = Inventory.query.filter_by(pos_item_id=item_data['id']).first()
            if item:
                # POS의 재고 수량과 현재 재고 수량 비교
                if item.quantity != item_data['quantity']:
                    # 차이만큼 재고 차감
                    diff = item.quantity - item_data['quantity']
                    if diff > 0:
                        consume_inventory(item.id, diff)
                        logger.info(f"POS 동기화: {item.name} {diff}{item.unit} 차감")
        
        return True, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"POS API 호출 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"재고 동기화 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

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
    
    # POS 시스템에 재고 차감 알림
    try:
        headers = {
            'Authorization': f'Bearer {Config.POS_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'item_id': stock.ingredient.pos_item_id,
            'quantity': quantity,
            'transaction_id': transaction.id
        }
        response = requests.post(
            f'{Config.POS_API_URL}/inventory/consume',
            headers=headers,
            json=data
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"POS 시스템 재고 차감 알림 실패: {str(e)}")
    
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

def consume_inventory(inventory_id: int, quantity: float) -> bool:
    """
    재고를 소비합니다.
    
    Args:
        inventory_id (int): 재고 ID
        quantity (float): 소비할 수량
        
    Returns:
        bool: 소비 성공 여부
    """
    try:
        inventory = Inventory.query.get(inventory_id)
        if not inventory:
            logger.warning(f"재고 ID {inventory_id}를 찾을 수 없습니다.")
            return False
            
        if inventory.quantity < quantity:
            send_notification(
                title="재고 부족 알림",
                message=f"{inventory.name}의 재고가 부족합니다.",
                level="warning"
            )
            logger.warning(f"재고 부족: {inventory.name} (현재: {inventory.quantity}, 필요: {quantity})")
            return False
            
        inventory.update_quantity(quantity, is_addition=False)
        logger.info(f"재고 소비: {inventory.name} ({quantity}{inventory.unit})")
        return True
        
    except Exception as e:
        logger.error(f"재고 소비 중 오류 발생: {str(e)}")
        db.session.rollback()
        return False

def check_low_stock():
    """
    부족 재고를 확인하고 알림을 발송합니다.
    """
    try:
        low_stock_items = Inventory.query.filter_by(status='부족').all()
        
        for item in low_stock_items:
            send_notification(
                title="재고 부족 알림",
                message=f"{item.name}의 재고가 부족합니다. 현재 수량: {item.quantity}{item.unit}",
                level="warning"
            )
            logger.warning(f"재고 부족 감지: {item.name} (현재: {item.quantity}{item.unit})")
            
    except Exception as e:
        logger.error(f"재고 확인 중 오류 발생: {str(e)}")
        db.session.rollback()

def get_inventory_status(item_name: str) -> dict:
    """
    특정 품목의 재고 상태 조회
    
    Returns:
        dict: 재고 상태 정보
    """
    try:
        item = Inventory.query.filter_by(name=item_name).first()
        if not item:
            return {
                'error': f"품목 '{item_name}'을(를) 찾을 수 없습니다."
            }
        
        return {
            'name': item.name,
            'quantity': item.quantity,
            'unit': item.unit,
            'status': item.status.value,
            'supplier': item.supplier,
            'last_order': {
                'date': item.orders[-1].order_date.strftime('%Y-%m-%d %H:%M:%S'),
                'quantity': item.orders[-1].quantity
            } if item.orders else None
        }
        
    except Exception as e:
        logger.error(f"재고 상태 조회 중 오류 발생: {str(e)}")
        return {
            'error': '재고 상태 조회에 실패했습니다.'
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

def check_inventory_status():
    """재고 상태 확인"""
    try:
        # 재고 부족 상태 확인
        low_stock_items = Inventory.query.filter_by(status='부족').all()
        for item in low_stock_items:
            alert = StockUsageAlert(
                item_id=item.id,
                alert_type='low_stock',
                message=f'{item.name}의 재고가 부족합니다. 현재 수량: {item.quantity}{item.unit}'
            )
            db.session.add(alert)
            
            # 관리자에게 알림 전송
            send_notification(
                title='재고 부족 알림',
                message=f'{item.name}의 재고가 부족합니다.\n현재 수량: {item.quantity}{item.unit}',
                level='warning'
            )
        
        # 유통기한 임박 상태 확인 (7일 이내)
        expiring_soon = datetime.now() + timedelta(days=7)
        expiring_items = Inventory.query.filter(
            Inventory.expiration_date <= expiring_soon,
            Inventory.expiration_date > datetime.now(),
            Inventory.is_disposed == False
        ).all()
        
        for item in expiring_items:
            days_left = (item.expiration_date - datetime.now()).days
            alert = StockUsageAlert(
                item_id=item.id,
                alert_type='expiring_soon',
                message=f'{item.name}의 유통기한이 {days_left}일 남았습니다.'
            )
            db.session.add(alert)
            
            # 관리자에게 알림 전송
            send_notification(
                title='유통기한 임박 알림',
                message=f'{item.name}의 유통기한이 {days_left}일 남았습니다.',
                level='warning'
            )
        
        db.session.commit()
        logger.info('재고 상태 확인이 완료되었습니다.')
    except Exception as e:
        logger.error(f'재고 상태 확인 중 오류 발생: {str(e)}')
        db.session.rollback()
        raise 