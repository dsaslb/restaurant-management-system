from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from extensions import db, migrate, login_manager
import os

# 환경 변수 로드
load_dotenv()

# 카카오 API 설정
KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
KAKAO_TEMPLATE_ID = os.getenv('KAKAO_TEMPLATE_ID')

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///restaurant.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models.employee import User
        return User.query.get(int(user_id))

    # 라우트 등록
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.employee import employee_bp
    from routes.schedule import schedule_bp
    from routes.inventory import inventory_bp
    from routes.notification import notification_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(schedule_bp, url_prefix='/schedule')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(notification_bp, url_prefix='/notification')

    @app.route('/')
    def index():
        return redirect(url_for('main.index'))

    # 초기 데이터 생성
    with app.app_context():
        db.create_all()
        from models.employee import User
        # 관리자 계정이 없으면 생성
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@restaurant.com',
                is_admin=True
            )
            admin.set_password('1234')
            db.session.add(admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)


