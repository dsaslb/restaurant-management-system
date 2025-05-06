from app import db, User
from werkzeug.security import generate_password_hash

def update_admin_password():
    admin = User.query.filter_by(username='admin01').first()
    if admin:
        admin.password = generate_password_hash('1234', method='pbkdf2:sha256', salt_length=8)
        db.session.commit()
        print("✅ 관리자(admin01) 비밀번호가 재설정되었습니다 (1234).")
    else:
        print("❌ 관리자 계정 'admin01'을 찾을 수 없습니다.")

if __name__ == '__main__':
    update_admin_password() 