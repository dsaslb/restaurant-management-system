from extensions import db
from datetime import datetime

class Order(db.Model):
    """발주 모델"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, completed, cancelled
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.DateTime)
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    item_name = db.Column(db.String(100), nullable=False)  # 품목 이름
    category = db.Column(db.String(50))                    # 카테고리 (예: 식자재, 주방용품 등)
    quantity = db.Column(db.Integer, nullable=False)       # 발주 수량
    expected_date = db.Column(db.Date)                     # 입고 예정일
    supplier = db.Column(db.String(100))                   # 업체명

    # 관계 설정
    user = db.relationship('User', back_populates='orders')
    supplier = db.relationship('Supplier', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    
    def calculate_total(self):
        """총 가격을 계산합니다."""
        return sum(item.total_price for item in self.items)
    
    def update_status(self, new_status):
        """발주 상태를 업데이트합니다."""
        valid_statuses = ['pending', 'approved', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            raise ValueError(f"유효하지 않은 상태입니다. 가능한 상태: {', '.join(valid_statuses)}")
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def can_cancel(self):
        """발주 취소 가능 여부를 확인합니다."""
        return self.status == 'pending'
    
    def can_update(self):
        """발주 수정 가능 여부를 확인합니다."""
        return self.status == 'pending'
    
    def __repr__(self):
        return f"<Order {self.id}>"

class OrderItem(db.Model):
    """발주 품목 모델"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    order = db.relationship('Order', back_populates='items')
    item = db.relationship('InventoryItem', back_populates='order_items')

    def __repr__(self):
        return f"<OrderItem {self.id}>" 