from app import create_app
from extensions import db
from models.employee import Employee
from models.inventory import InventoryItem

app = create_app()

with app.app_context():
    # 예시 직원 데이터 추가
    employee1 = Employee(user_id=1, name='홍길동', position='매니저')
    employee2 = Employee(user_id=2, name='김철수', position='요리사')
    db.session.add(employee1)
    db.session.add(employee2)

    # 예시 물품 데이터 추가
    item1 = InventoryItem(name='쌀', unit='kg', min_quantity=10, current_quantity=50)
    item2 = InventoryItem(name='고기', unit='kg', min_quantity=5, current_quantity=20)
    db.session.add(item1)
    db.session.add(item2)

    # 변경 사항 커밋
    db.session.commit() 