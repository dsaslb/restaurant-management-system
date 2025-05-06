from app import db, User
from werkzeug.security import generate_password_hash

def init_admin_password():
    # 관리자 계정이 없으면 생성
    admin = User.query.filter_by(username='admin01').first()
    if not admin:
        admin = User(
            username='admin01',
            password=generate_password_hash('1234', method='pbkdf2:sha256', salt_length=8),
            name='관리자',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ 관리자 계정이 생성되었습니다.")
        print("   - 사용자명: admin01")
        print("   - 비밀번호: 1234")
    else:
        # 관리자 계정이 있으면 비밀번호만 재설정
        admin.password = generate_password_hash('1234', method='pbkdf2:sha256', salt_length=8)
        db.session.commit()
        print("✅ 관리자 비밀번호가 재설정되었습니다.")
        print("   - 사용자명: admin01")
        print("   - 비밀번호: 1234")

if __name__ == '__main__':
    init_admin_password() 