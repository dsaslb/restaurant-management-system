from datetime import datetime
from extensions import db

class Notification(db.Model):
    """알림 모델"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # '재고부족', '유통기한', '발주' 등
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = db.relationship('User', back_populates='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

class AlertLog(db.Model):
    """알림 로그 모델"""
    __tablename__ = 'alert_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'))
    alert_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    notification = db.relationship('Notification')
    
    def __repr__(self):
        return f'<AlertLog {self.id}: {self.alert_type}>'

class NotificationSetting(db.Model):
    """알림 설정 모델"""
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # email, sms, push
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = db.relationship('User', backref=db.backref('notification_settings', lazy=True))
    
    def __repr__(self):
        return f'<NotificationSetting {self.user_id} - {self.notification_type}>'

class NotificationLog(db.Model):
    """알림 로그 모델"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'), nullable=False)
    delivery_status = db.Column(db.String(20))  # sent, failed, delivered
    delivery_time = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    notification = db.relationship('Notification', backref=db.backref('logs', lazy=True))
    
    def __repr__(self):
        return f'<NotificationLog {self.notification_id} - {self.delivery_status}>' 