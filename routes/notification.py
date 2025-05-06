from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, Notification
from datetime import datetime

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/')
@login_required
def index():
    """알림 목록 페이지"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .all()
    return render_template('notification/index.html', notifications=notifications)

@notification_bp.route('/api/notifications')
@login_required
def get_notifications():
    """알림 목록 API"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .all()
    return jsonify({
        'status': 'success',
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': n.is_read
        } for n in notifications]
    })

@notification_bp.route('/api/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """알림 읽음 처리"""
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': '권한이 없습니다.'}), 403
    
    notification.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'}) 