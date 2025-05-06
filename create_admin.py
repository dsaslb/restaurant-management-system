from app import create_app
from extensions import db
from models.employee import User, Employee

def create_admin():
    app = create_app()
    with app.app_context():
        # 관리자 사용자 생성
        admin_user = User(
            username='admin01',
            email='admin@example.com',
            is_admin=True
        )
        admin_user.set_password('admin1234')
        
        # 관리자 직원 정보 생성
        admin_employee = Employee(
            name='관리자',
            phone='010-1234-5678',
            position='관리자'
        )
        
        # 관계 설정
        admin_user.employee = admin_employee
        
        # 데이터베이스에 저장
        db.session.add(admin_user)
        db.session.commit()
        
        print('관리자 계정이 생성되었습니다.')
        print('사용자 이름: admin01')
        print('비밀번호: admin1234')

if __name__ == '__main__':
    create_admin() 