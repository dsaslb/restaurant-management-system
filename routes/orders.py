from flask import Blueprint, render_template, request, jsonify, current_app
from models.inventory import Inventory, Order, ProductCategory, InventoryStatus
from database import db
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from utils.notification import send_notification

logger = logging.getLogger(__name__)
orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders')
def order_list():
    """발주 목록 페이지"""
    try:
        # 발주 목록 조회
        orders = Order.query.order_by(Order.order_date.desc()).all()
        
        # 재고 상태 확인
        for order in orders:
            order.inventory.check_status()
        
        return render_template('orders/list.html', orders=orders)
        
    except Exception as e:
        logger.error(f"발주 목록 조회 중 오류 발생: {str(e)}")
        return render_template('error.html', error="발주 목록을 불러오는데 실패했습니다.")

@orders_bp.route('/orders/create', methods=['GET', 'POST'])
def create_order():
    """발주 생성"""
    try:
        if request.method == 'POST':
            data = request.form
            
            # 발주 정보 검증
            if not all(k in data for k in ['inventory_id', 'quantity', 'delivery_date']):
                return jsonify({'error': '필수 정보가 누락되었습니다.'}), 400
            
            # 재고 확인
            inventory = Inventory.query.get(data['inventory_id'])
            if not inventory:
                return jsonify({'error': '존재하지 않는 재고입니다.'}), 404
            
            # 발주 생성
            order = Order(
                inventory_id=inventory.id,
                quantity=int(data['quantity']),
                delivery_date=datetime.strptime(data['delivery_date'], '%Y-%m-%d'),
                status='대기중'
            )
            
            db.session.add(order)
            db.session.commit()
            
            # 알림 발송
            send_notification(
                title="새로운 발주 요청",
                message=f"{inventory.name} {order.quantity}{inventory.unit} 발주 요청이 등록되었습니다.",
                level="info"
            )
            
            return jsonify({'message': '발주가 등록되었습니다.'})
        
        # GET 요청 처리
        inventories = Inventory.query.filter_by(status=InventoryStatus.LOW).all()
        return render_template('orders/create.html', inventories=inventories)
        
    except Exception as e:
        logger.error(f"발주 생성 중 오류 발생: {str(e)}")
        return jsonify({'error': '발주 등록에 실패했습니다.'}), 500

@orders_bp.route('/orders/<int:order_id>/update', methods=['POST'])
def update_order(order_id: int):
    """발주 상태 업데이트"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.form
        
        if 'status' not in data:
            return jsonify({'error': '상태 정보가 누락되었습니다.'}), 400
        
        # 상태 업데이트
        order.status = data['status']
        
        # 입고 처리
        if data['status'] == '입고완료':
            order.inventory.update_quantity(order.quantity, is_addition=True)
            
            # 알림 발송
            send_notification(
                title="발주 입고 완료",
                message=f"{order.inventory.name} {order.quantity}{order.inventory.unit} 입고가 완료되었습니다.",
                level="success"
            )
        
        db.session.commit()
        return jsonify({'message': '발주 상태가 업데이트되었습니다.'})
        
    except Exception as e:
        logger.error(f"발주 상태 업데이트 중 오류 발생: {str(e)}")
        return jsonify({'error': '발주 상태 업데이트에 실패했습니다.'}), 500

@orders_bp.route('/orders/check')
def check_orders():
    """발주 체크"""
    try:
        # 미발주 재고 확인
        low_stock = Inventory.query.filter_by(status=InventoryStatus.LOW).all()
        
        # 발주 마감 시간 체크
        now = datetime.utcnow()
        cutoff_time = now.replace(hour=17, minute=30, second=0, microsecond=0)
        
        if now >= cutoff_time:
            # 미발주 항목 알림
            for item in low_stock:
                if not item.orders or all(order.status != '대기중' for order in item.orders):
                    send_notification(
                        title="발주 미진행 알림",
                        message=f"{item.name}의 발주가 아직 진행되지 않았습니다.",
                        level="warning"
                    )
        
        return jsonify({'message': '발주 체크가 완료되었습니다.'})
        
    except Exception as e:
        logger.error(f"발주 체크 중 오류 발생: {str(e)}")
        return jsonify({'error': '발주 체크에 실패했습니다.'}), 500

@orders_bp.route('/orders/statistics')
def order_statistics():
    """발주 통계"""
    try:
        # 기간 설정
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # 카테고리별 발주 금액
        category_stats = {}
        for category in ProductCategory:
            orders = Order.query.join(Inventory).filter(
                Order.order_date.between(start_date, end_date),
                Inventory.category == category
            ).all()
            
            total_amount = sum(order.quantity * order.inventory.price for order in orders)
            category_stats[category.value] = total_amount
        
        # 업체별 발주 횟수
        supplier_stats = {}
        orders = Order.query.join(Inventory).filter(
            Order.order_date.between(start_date, end_date)
        ).all()
        
        for order in orders:
            supplier = order.inventory.supplier
            if supplier:
                supplier_stats[supplier] = supplier_stats.get(supplier, 0) + 1
        
        return render_template(
            'orders/statistics.html',
            category_stats=category_stats,
            supplier_stats=supplier_stats
        )
        
    except Exception as e:
        logger.error(f"발주 통계 조회 중 오류 발생: {str(e)}")
        return render_template('error.html', error="발주 통계를 불러오는데 실패했습니다.")

@orders_bp.route('/orders/statistics/filter', methods=['POST'])
def filter_order_statistics():
    """기간별 발주 통계 필터링"""
    try:
        data = request.get_json()
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        
        # 카테고리별 발주 금액
        category_stats = {}
        for category in ProductCategory:
            orders = Order.query.join(Inventory).filter(
                Order.order_date.between(start_date, end_date),
                Inventory.category == category
            ).all()
            
            total_amount = sum(order.quantity * order.inventory.price for order in orders)
            category_stats[category.value] = total_amount
        
        # 업체별 발주 횟수
        supplier_stats = {}
        orders = Order.query.join(Inventory).filter(
            Order.order_date.between(start_date, end_date)
        ).all()
        
        for order in orders:
            supplier = order.inventory.supplier
            if supplier:
                supplier_stats[supplier] = supplier_stats.get(supplier, 0) + 1
        
        # 일별 발주 추이
        daily_stats = {}
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            daily_orders = Order.query.filter(
                Order.order_date.between(current_date, next_date)
            ).all()
            
            daily_stats[current_date.strftime('%Y-%m-%d')] = {
                'count': len(daily_orders),
                'amount': sum(order.quantity * order.inventory.price for order in daily_orders)
            }
            
            current_date = next_date
        
        return jsonify({
            'category_stats': category_stats,
            'supplier_stats': supplier_stats,
            'daily_stats': daily_stats
        })
        
    except Exception as e:
        logger.error(f"발주 통계 필터링 중 오류 발생: {str(e)}")
        return jsonify({'error': '통계 필터링에 실패했습니다.'}), 500 