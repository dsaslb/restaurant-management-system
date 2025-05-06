from app import create_app
from extensions import db
from models.employee import Employee
from models.inventory import InventoryItem
from datetime import date, timedelta
from utils.inventory import register_inventory, consume_inventory

app = create_app()

def add_sample_items():
    """테스트용 품목 데이터 추가"""
    print("테스트용 품목 데이터 추가 중...")
    
    items = [
        InventoryItem(name='닭고기', unit='개', min_quantity=3, category='육류'),
        InventoryItem(name='돼지고기', unit='kg', min_quantity=5, category='육류'),
        InventoryItem(name='쌀', unit='kg', min_quantity=20, category='곡물'),
        InventoryItem(name='계란', unit='개', min_quantity=10, category='유제품')
    ]
    
    for item in items:
        existing = InventoryItem.query.filter_by(name=item.name).first()
        if not existing:
            db.session.add(item)
            print(f"품목 추가: {item.name}")
    
    db.session.commit()
    print("테스트용 품목 데이터 추가 완료!")

def add_sample_inventory_data():
    """테스트용 재고 데이터 추가"""
    print("\n테스트용 재고 데이터 추가 중...")
    
    # 닭고기 재고 테스트
    print("\n1. 닭고기 재고 테스트")
    # 5개 입고: 유통기한 5월 10일
    success, msg = register_inventory("닭고기", 5, date(2025, 5, 10), "농협", 5000)
    print(f"닭고기 5개 입고: {'성공' if success else f'실패 - {msg}'}")
    
    # 10개 입고: 유통기한 5월 13일
    success, msg = register_inventory("닭고기", 10, date(2025, 5, 13), "농협", 4800)
    print(f"닭고기 10개 입고: {'성공' if success else f'실패 - {msg}'}")
    
    # 7개 출고 (FIFO)
    success, msg = consume_inventory("닭고기", 7, "테스트 출고")
    print(f"닭고기 7개 출고: {'성공' if success else f'실패 - {msg}'}")
    
    # 돼지고기 재고 테스트
    print("\n2. 돼지고기 재고 테스트")
    # 20kg 입고: 유통기한 5월 15일
    success, msg = register_inventory("돼지고기", 20, date(2025, 5, 15), "축협", 12000)
    print(f"돼지고기 20kg 입고: {'성공' if success else f'실패 - {msg}'}")
    
    # 15kg 입고: 유통기한 5월 20일
    success, msg = register_inventory("돼지고기", 15, date(2025, 5, 20), "축협", 11500)
    print(f"돼지고기 15kg 입고: {'성공' if success else f'실패 - {msg}'}")
    
    # 25kg 출고 (FIFO)
    success, msg = consume_inventory("돼지고기", 25, "테스트 출고")
    print(f"돼지고기 25kg 출고: {'성공' if success else f'실패 - {msg}'}")
    
    # 쌀 재고 테스트
    print("\n3. 쌀 재고 테스트")
    # 100kg 입고: 유통기한 2026년 5월 1일
    success, msg = register_inventory("쌀", 100, date(2026, 5, 1), "농협", 80000)
    print(f"쌀 100kg 입고: {'성공' if success else f'실패 - {msg}'}")
    
    # 50kg 입고: 유통기한 2026년 6월 1일
    success, msg = register_inventory("쌀", 50, date(2026, 6, 1), "농협", 82000)
    print(f"쌀 50kg 입고: {'성공' if success else f'실패 - {msg}'}")
    
    # 30kg 출고 (FIFO)
    success, msg = consume_inventory("쌀", 30, "테스트 출고")
    print(f"쌀 30kg 출고: {'성공' if success else f'실패 - {msg}'}")
    
    # 유통기한 임박 테스트
    print("\n4. 유통기한 임박 테스트")
    # 10개 입고: 유통기한 7일 후
    success, msg = register_inventory("계란", 10, date.today() + timedelta(days=7), "농가", 3000)
    print(f"계란 10개 입고 (유통기한 7일): {'성공' if success else f'실패 - {msg}'}")
    
    # 5개 입고: 유통기한 14일 후
    success, msg = register_inventory("계란", 5, date.today() + timedelta(days=14), "농가", 3200)
    print(f"계란 5개 입고 (유통기한 14일): {'성공' if success else f'실패 - {msg}'}")
    
    print("\n테스트용 재고 데이터 추가 완료!")

if __name__ == "__main__":
    with app.app_context():
        add_sample_items()
        add_sample_inventory_data() 