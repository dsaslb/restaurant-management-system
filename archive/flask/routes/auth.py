from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps
from typing import Optional
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# JWT 설정
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(hours=1)

logger = logging.getLogger(__name__)

def create_admin_user():
    """관리자 계정 생성"""
    admin = User.query.filter_by(username='admin01').first()
    if not admin:
        admin = User(
            username='admin01',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()
        print("관리자 계정이 생성되었습니다.")

def create_jwt_token(user_id: int) -> str:
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[int]:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """JWT 토큰 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'status': 'error', 'message': '토큰이 필요합니다.'}), 401
            
        token = token.replace('Bearer ', '')
        user_id = verify_jwt_token(token)
        if not user_id:
            return jsonify({'status': 'error', 'message': '유효하지 않은 토큰입니다.'}), 401
            
        return f(user_id, *args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """로그인"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.info(f'로그인 시도: {username}')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            logger.info(f'사용자 찾음: {user.username}, is_active={user.is_active}')
            
            if not user.is_active:
                logger.warning(f'비활성화된 계정: {username}')
                flash('비활성화된 계정입니다.', 'error')
                return render_template('auth/login.html')
            
            if user.check_password(password):
                logger.info(f'로그인 성공: {username}')
                login_user(user)
                flash('로그인되었습니다.', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                logger.warning(f'비밀번호 불일치: {username}')
        else:
            logger.warning(f'사용자를 찾을 수 없음: {username}')
        
        flash('잘못된 사용자 이름 또는 비밀번호입니다.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """로그아웃"""
    logout_user()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """회원가입"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('이미 사용 중인 사용자 이름입니다.', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('이미 사용 중인 이메일입니다.', 'error')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다. 로그인해주세요.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html') 