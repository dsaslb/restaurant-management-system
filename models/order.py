from extensions import db
from datetime import datetime

class Order(db.Model):
    """발주 모델"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='대기중')  # 대기중, 발주완료, 입고완료
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    delivery_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    user = db.relationship('User', back_populates='orders')
    supplier = db.relationship('Supplier', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    
    def calculate_total(self):
        """총 가격을 계산합니다."""
        return sum(item.total_price for item in self.items)
    
    def update_status(self, new_status):
        """주문 상태를 업데이트합니다."""
        valid_statuses = ['대기중', '발주완료', '입고완료']
        if new_status not in valid_statuses:
            raise ValueError(f"유효하지 않은 상태입니다. 가능한 상태: {', '.join(valid_statuses)}")
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def can_cancel(self):
        """발주 취소 가능 여부를 확인합니다."""
        return self.status == '대기중'
    
    def can_update(self):
        """발주 수정 가능 여부를 확인합니다."""
        return self.status == '대기중'
    
    def __repr__(self):
        return f'<Order {self.id}: {self.status}>'

class OrderItem(db.Model):
    """주문 항목 모델"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    order = db.relationship('Order', back_populates='items')
    item = db.relationship('InventoryItem')

    def __repr__(self):
        return f'<OrderItem {self.id}>' 