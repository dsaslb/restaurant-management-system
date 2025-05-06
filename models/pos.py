from datetime import datetime
from extensions import db
import json

class POSSaleLog(db.Model):
    """POS 판매 로그 모델"""
    __tablename__ = 'pos_sale_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.String(50), nullable=False, unique=True)
    pos_store_id = db.Column(db.String(50), nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='success')  # success, failed, partial
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    items = db.relationship('POSSaleItem', back_populates='sale_log')
    
    def __repr__(self):
        return f'<POSSaleLog {self.sale_id}>'

class POSSaleItem(db.Model):
    """POS 판매 항목 모델"""
    __tablename__ = 'pos_sale_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_log_id = db.Column(db.Integer, db.ForeignKey('pos_sale_logs.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, default=0)
    
    # 관계 설정
    sale_log = db.relationship('POSSaleLog', back_populates='items')
    item = db.relationship('Inventory')
    
    def __repr__(self):
        return f'<POSSaleItem {self.id}>'

class POSPerformanceLog(db.Model):
    """POS 성과 로그 모델"""
    __tablename__ = 'pos_performance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_sales = db.Column(db.Float, nullable=False)
    total_orders = db.Column(db.Integer, nullable=False)
    average_order_value = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<POSPerformanceLog {self.id}>' 