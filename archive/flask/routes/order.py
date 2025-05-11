from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.order import Order, OrderItem
from datetime import datetime
from models.inventory import InventoryItem
from extensions import db
from utils.decorators import admin_required
from models import Supplier
from typing import Dict, Any, Optional

order_bp = Blueprint('order', __name__, url_prefix='/orders')

def validate_order_data(data: Dict[str, Any]) -> Optional[str]:
    """발주 데이터 유효성 검사"""
    required_fields = ['item_id', 'supplier_id', 'quantity', 'unit_price']
    for field in required_fields:
        if field not in data:
            return f"{field}는 필수 항목입니다."
    
    try:
        quantity = int(data['quantity'])
        unit_price = float(data['unit_price'])
        if quantity <= 0:
            return "수량은 0보다 커야 합니다."
        if unit_price < 0:
            return "단가는 0 이상이어야 합니다."
    except (ValueError, TypeError):
        return "수량과 단가는 숫자여야 합니다."
    
    return None

@order_bp.route('/')
@login_required
def order_list():
    """발주 목록 조회"""
    try:
        # 필터링 옵션
        status = request.args.get('status')
        supplier_id = request.args.get('supplier_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 기본 쿼리
        query = Order.query
        
        # 필터 적용
        if status:
            query = query.filter(Order.status == status)
        if supplier_id:
            query = query.filter(Order.supplier_id == supplier_id)
        if start_date:
            query = query.filter(Order.order_date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Order.order_date <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        # 정렬
        query = query.order_by(Order.created_at.desc())
        
        orders = query.all()
        return render_template('orders/order_list.html', orders=orders)
    except Exception as e:
        flash(f'발주 목록 조회 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@order_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_order():
    """새 발주 생성"""
    if request.method == 'POST':
        try:
            # 발주 생성
            order = Order(
                user_id=current_user.id,
                supplier_id=request.form['supplier_id'],
                delivery_date=datetime.strptime(request.form['delivery_date'], '%Y-%m-%d'),
                notes=request.form.get('notes')
            )
            db.session.add(order)
            db.session.flush()  # ID 생성

            # 발주 품목 추가
            total_amount = 0
            for item_id, quantity in zip(
                request.form.getlist('item_id[]'),
                request.form.getlist('quantity[]')
            ):
                if not item_id or not quantity:
                    continue

                inventory_item = InventoryItem.query.get(item_id)
                if not inventory_item:
                    continue

                quantity = int(quantity)
                unit_price = inventory_item.unit_price
                total_price = quantity * unit_price
                total_amount += total_price

                order_item = OrderItem(
                    order_id=order.id,
                    item_id=item_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                db.session.add(order_item)

            order.total_amount = total_amount
            db.session.commit()
            flash('발주가 성공적으로 등록되었습니다.', 'success')
            return redirect(url_for('order.order_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'발주 등록 중 오류가 발생했습니다: {str(e)}', 'error')

    # GET 요청 처리
    inventory_items = InventoryItem.query.all()
    suppliers = Supplier.query.all()
    return render_template('orders/order_form.html',
                         inventory_items=inventory_items,
                         suppliers=suppliers)

@order_bp.route('/<int:order_id>')
@login_required
def view_order(order_id):
    """발주 상세 조회"""
    order = Order.query.get_or_404(order_id)
    return render_template('orders/order_detail.html', order=order)

@order_bp.route('/<int:order_id>/update', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    """발주 상태 업데이트"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    try:
        order.update_status(new_status)
        db.session.commit()
        flash('발주 상태가 업데이트되었습니다.', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'상태 업데이트 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(url_for('order.view_order', order_id=order_id))

@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_order(order_id):
    """발주 취소"""
    order = Order.query.get_or_404(order_id)
    
    if not order.can_cancel():
        flash('취소할 수 없는 발주입니다.', 'error')
        return redirect(url_for('order.view_order', order_id=order_id))
    
    try:
        order.status = 'cancelled'
        db.session.commit()
        flash('발주가 취소되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'발주 취소 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(url_for('order.order_list')) 