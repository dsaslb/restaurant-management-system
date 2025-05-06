from datetime import datetime
from extensions import db

class Supplier(db.Model):
    """공급업체 모델"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(200))            # 이메일/전화번호/웹사이트 등
    order_method = db.Column(db.String(50))        # 'email', 'sms', 'web'
    default_lead_days = db.Column(db.Integer)      # D-1, D-2용 기본값
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # 관계 설정
    orders = db.relationship('Order', back_populates='supplier')
    
    def get_active_orders(self):
        """활성화된 발주 목록을 반환합니다."""
        return [order for order in self.orders if order.status == '대기중']
    
    def get_order_history(self, days=30):
        """최근 발주 이력을 반환합니다."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [order for order in self.orders if order.ordered_at >= cutoff_date]
    
    def __repr__(self):
        return f'<Supplier {self.name}>' 