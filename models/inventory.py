from extensions import db
from datetime import datetime, date
from sqlalchemy import CheckConstraint

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit = db.Column(db.String(20), nullable=False)
    min_quantity = db.Column(db.Integer, default=0)
    max_quantity = db.Column(db.Float)
    current_quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    batches = db.relationship('InventoryBatch', backref='item', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        CheckConstraint('min_quantity >= 0', name='check_min_quantity_positive'),
        CheckConstraint('current_quantity >= 0', name='check_current_quantity_positive'),
    )

    def update_current_quantity(self):
        """현재 재고 수량을 모든 배치의 가용 수량 합계로 업데이트"""
        self.current_quantity = sum(batch.available_quantity for batch in self.batches)
        return self.current_quantity

    def __repr__(self):
        return f'<InventoryItem {self.name}>'

class InventoryBatch(db.Model):
    __tablename__ = 'inventory_batches'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False)
    batch_number = db.Column(db.String(50), unique=True)
    received_date = db.Column(db.Date, default=date.today)
    expiration_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    used_quantity = db.Column(db.Integer, default=0)
    supplier = db.Column(db.String(100))
    purchase_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('used_quantity >= 0', name='check_used_quantity_positive'),
        CheckConstraint('used_quantity <= quantity', name='check_used_quantity_not_exceed_quantity'),
    )

    @property
    def available_quantity(self):
        """가용 수량 계산"""
        return self.quantity - self.used_quantity

    @property
    def is_expired(self):
        """유통기한 만료 여부 확인"""
        return date.today() > self.expiration_date

    @property
    def days_until_expiration(self):
        """유통기한까지 남은 일수 계산"""
        return (self.expiration_date - date.today()).days

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    min_quantity = db.Column(db.Float, default=0)
    max_quantity = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stock_item = db.relationship('StockItem', backref='ingredient', uselist=False)
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, received
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ingredient = db.relationship('Ingredient', backref='orders')
    
    def __repr__(self):
        return f'<OrderItem {self.id}: {self.ingredient.name}>'

class StockItem(db.Model):
    __tablename__ = 'stock_items'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StockItem {self.id}: {self.ingredient.name}>'

class StockTransaction(db.Model):
    __tablename__ = 'stock_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 입고, 출고
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    ingredient = db.relationship('Ingredient', backref='transactions')
    
    def __repr__(self):
        return f'<StockTransaction {self.id}: {self.ingredient.name}>'

class StockUsageAlert(db.Model):
    __tablename__ = 'stock_usage_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ingredient = db.relationship('Ingredient', backref='usage_alerts')
    
    def __repr__(self):
        return f'<StockUsageAlert {self.id}: {self.ingredient.name}>'



