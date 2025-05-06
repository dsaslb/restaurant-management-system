from datetime import datetime, date, timedelta
from sqlalchemy import CheckConstraint, Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from extensions import db
import enum
import logging
from models.recipe import Recipe

logger = logging.getLogger(__name__)

class ProductCategory(enum.Enum):
    """제품 카테고리"""
    HALL = "홀용"
    KITCHEN = "주방용"
    TABLEWARE = "식기류"

class InventoryStatus(enum.Enum):
    """재고 상태"""
    NORMAL = "정상"
    LOW = "부족"
    EXPIRED = "유통기한 지남"
    DISPOSED = "폐기"

class InventoryItem(db.Model):
    """재고 품목 모델"""
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))            # '홀용', '주방용', '식기류'
    unit = db.Column(db.String(20))                # 'kg', '개', '박스' 등
    min_quantity = db.Column(db.Integer, nullable=False)
    current_quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float)                # 단가
    origin = db.Column(db.String(100))             # 원산지
    expiration_date = db.Column(db.Date)           # 유통기한
    storage_info = db.Column(db.String(200))       # 보관 방법
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))  # 공급업체 ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # 관계 설정
    order_items = db.relationship('OrderItem', back_populates='item')
    batches = db.relationship('InventoryBatch', back_populates='item', cascade='all, delete-orphan')
    ingredients = db.relationship('Ingredient', back_populates='item')
    stock_items = db.relationship('StockItem', back_populates='item')
    supplier = db.relationship('Supplier', back_populates='inventory_items')
    
    def check_stock_level(self):
        """재고 수준을 확인하고 부족 여부를 반환합니다."""
        return self.current_quantity <= self.min_quantity
    
    def update_quantity(self, quantity, is_addition=True):
        """재고 수량을 업데이트합니다."""
        if is_addition:
            self.current_quantity += quantity
        else:
            if self.current_quantity < quantity:
                raise ValueError("재고가 부족합니다.")
            self.current_quantity -= quantity
        self.updated_at = datetime.utcnow()
    
    def check_expiration(self):
        """유통기한 상태를 확인합니다."""
        if not self.expiration_date:
            return None
        
        today = date.today()
        days_until_expiry = (self.expiration_date - today).days
        
        if days_until_expiry < 0:
            return "만료"
        elif days_until_expiry <= 3:
            return "임박"
        return "정상"
    
    def __repr__(self):
        return f'<InventoryItem {self.name}>'

class InventoryBatch(db.Model):
    """재고 배치 모델"""
    __tablename__ = 'inventory_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    batch_number = db.Column(db.String(50), unique=True)
    quantity = db.Column(db.Float, nullable=False)
    used_quantity = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float)
    supplier = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    item = db.relationship('InventoryItem', back_populates='batches')
    
    @property
    def expire_soon(self):
        """유통기한이 3일 이내로 남았는지 확인"""
        if not self.expiration_date:
            return False
        return self.expiration_date <= datetime.now().date() + timedelta(days=3)
    
    def __repr__(self):
        return f'<InventoryBatch {self.batch_number}>'

class Ingredient(db.Model):
    """재료 모델"""
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    
    # 관계 설정
    item = db.relationship('InventoryItem', back_populates='ingredients')
    recipes = db.relationship('RecipeIngredient', back_populates='ingredient')
    
    def __repr__(self):
        return f'<Ingredient {self.id}>'

class StockItem(db.Model):
    """재고 항목 모델"""
    __tablename__ = 'stock_items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    location = db.Column(db.String(100))
    last_checked = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    item = db.relationship('InventoryItem', back_populates='stock_items')
    transactions = db.relationship('StockTransaction', back_populates='stock_item')
    
    def __repr__(self):
        return f'<StockItem {self.id}>'

class StockTransaction(db.Model):
    """재고 거래 모델"""
    __tablename__ = 'stock_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_items.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # in, out, adjust
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    reference = db.Column(db.String(100))  # 주문 번호, 조정 사유 등
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    stock_item = db.relationship('StockItem', back_populates='transactions')
    
    def __repr__(self):
        return f'<StockTransaction {self.id}>'

class StockUsageAlert(db.Model):
    """재고 사용 알림 모델"""
    __tablename__ = 'stock_usage_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # low, high, expiration
    message = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StockUsageAlert {self.id}>'

class Inventory(db.Model):
    """재고 모델"""
    __tablename__ = "inventory"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum(ProductCategory), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100))
    origin = db.Column(db.String(100))
    storage_method = db.Column(db.String(100))
    expiration_date = db.Column(db.DateTime)
    status = db.Column(db.Enum(InventoryStatus), default=InventoryStatus.NORMAL)
    is_disposed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    disposals = db.relationship("Disposal", back_populates="inventory")
    
    def check_status(self) -> None:
        """재고 상태를 확인하고 업데이트합니다."""
        try:
            # 유통기한 체크
            if self.expiration_date:
                days_until_expiry = (self.expiration_date - datetime.utcnow()).days
                
                if days_until_expiry < 0:
                    self.status = InventoryStatus.EXPIRED
                    logger.warning(f"유통기한 지남: {self.name}")
                    return
                
                if days_until_expiry <= 3:
                    self.status = InventoryStatus.LOW
                    logger.warning(f"유통기한 임박: {self.name} (D-{days_until_expiry})")
                    return
            
            # 재고량 체크
            if self.quantity <= 0:
                self.status = InventoryStatus.LOW
                logger.warning(f"재고 부족: {self.name}")
                return
            
            self.status = InventoryStatus.NORMAL
            
        except Exception as e:
            logger.error(f"재고 상태 확인 중 오류 발생: {str(e)}")
            raise
    
    def dispose(self, reason: str) -> None:
        """
        재고를 폐기 처리합니다.
        
        Args:
            reason (str): 폐기 사유
        """
        try:
            self.is_disposed = True
            self.status = InventoryStatus.DISPOSED
            
            # 폐기 기록 생성
            disposal = Disposal(
                inventory_id=self.id,
                reason=reason,
                quantity=self.quantity
            )
            
            # 재고량 초기화
            self.quantity = 0
            
            logger.info(f"재고 폐기 처리: {self.name} (사유: {reason})")
            
        except Exception as e:
            logger.error(f"재고 폐기 처리 중 오류 발생: {str(e)}")
            raise
    
    def update_quantity(self, quantity: int, is_addition: bool = True) -> None:
        """
        재고량을 업데이트합니다.
        
        Args:
            quantity (int): 변경할 수량
            is_addition (bool): True면 증가, False면 감소
        """
        try:
            if is_addition:
                self.quantity += quantity
            else:
                if self.quantity < quantity:
                    raise ValueError("재고량이 부족합니다.")
                self.quantity -= quantity
            
            self.check_status()
            logger.info(f"재고량 업데이트: {self.name} ({'+' if is_addition else '-'}{quantity})")
            
        except Exception as e:
            logger.error(f"재고량 업데이트 중 오류 발생: {str(e)}")
            raise

class Disposal(db.Model):
    """폐기 모델"""
    __tablename__ = "disposals"
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"))
    reason = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    disposal_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계
    inventory = db.relationship("Inventory", back_populates="disposals")



