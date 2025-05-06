import unittest
from datetime import date, timedelta
from app import create_app
from extensions import db
from models.inventory import InventoryItem, InventoryBatch
from utils.inventory import (
    register_inventory,
    consume_inventory,
    get_inventory_status,
    check_inventory_availability
)

class TestInventorySystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_inventory(self):
        """재고 등록 테스트"""
        # 품목 생성
        item = InventoryItem(name='테스트품목', unit='개', min_quantity=5)
        db.session.add(item)
        db.session.commit()

        # 재고 등록
        success, msg = register_inventory(
            '테스트품목',
            10,
            date.today() + timedelta(days=30),
            '테스트공급업체',
            1000
        )
        self.assertTrue(success)
        self.assertIsNone(msg)

        # 재고 확인
        item = InventoryItem.query.filter_by(name='테스트품목').first()
        self.assertEqual(item.current_quantity, 10)

    def test_consume_inventory_fifo(self):
        """FIFO 방식 재고 출고 테스트"""
        # 품목 생성
        item = InventoryItem(name='테스트품목', unit='개', min_quantity=5)
        db.session.add(item)
        db.session.commit()

        # 두 개의 배치 등록
        register_inventory('테스트품목', 5, date.today() + timedelta(days=10))
        register_inventory('테스트품목', 10, date.today() + timedelta(days=20))

        # 7개 출고
        success, msg = consume_inventory('테스트품목', 7, '테스트출고')
        self.assertTrue(success)
        self.assertIsNone(msg)

        # 첫 번째 배치가 모두 소진되었는지 확인
        batches = InventoryBatch.query.filter_by(item_id=item.id).order_by(InventoryBatch.expiration_date).all()
        self.assertEqual(batches[0].used_quantity, 5)
        self.assertEqual(batches[1].used_quantity, 2)

    def test_inventory_status(self):
        """재고 상태 조회 테스트"""
        # 품목 생성 및 재고 등록
        item = InventoryItem(name='테스트품목', unit='개', min_quantity=5)
        db.session.add(item)
        db.session.commit()

        register_inventory('테스트품목', 10, date.today() + timedelta(days=7))
        register_inventory('테스트품목', 5, date.today() + timedelta(days=14))

        # 재고 상태 조회
        status = get_inventory_status('테스트품목')
        self.assertEqual(status['total_available'], 15)
        self.assertEqual(len(status['expiring_soon']), 1)

    def test_low_stock_alert(self):
        """재고 부족 알림 테스트"""
        # 품목 생성
        item = InventoryItem(name='테스트품목', unit='개', min_quantity=5)
        db.session.add(item)
        db.session.commit()

        # 최소 재고량보다 적은 수량 등록
        register_inventory('테스트품목', 3, date.today() + timedelta(days=30))

        # 재고 상태 확인
        status = get_inventory_status('테스트품목')
        self.assertTrue(status['is_low_stock'])

    def test_expired_inventory(self):
        """유통기한 만료 테스트"""
        # 품목 생성
        item = InventoryItem(name='테스트품목', unit='개', min_quantity=5)
        db.session.add(item)
        db.session.commit()

        # 유통기한이 지난 배치 등록
        register_inventory('테스트품목', 5, date.today() - timedelta(days=1))

        # 재고 상태 확인
        status = get_inventory_status('테스트품목')
        self.assertEqual(status['total_available'], 0)

if __name__ == '__main__':
    unittest.main() 