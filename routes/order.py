from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.order import Order, OrderItem
from datetime import datetime, date, timedelta
from models.inventory import InventoryItem, InventoryBatch
from extensions import db
from utils.decorators import admin_required
from utils.inventory import consume_inventory, sync_pos_inventory
from models import Supplier
from typing import Dict, Any, Optional

bp = Blueprint('order', __name__, url_prefix='/order')

@bp.route('/')
@login_required
def index():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('order/index.html', orders=orders)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        # 주문 생성 로직
        pass
    return render_template('order/create.html')

@bp.route('/<int:order_id>')
@login_required
def view(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order/view.html', order=order)

@bp.route('/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        # 주문 수정 로직
        pass
    return render_template('order/edit.html', order=order)

@bp.route('/<int:order_id>/delete', methods=['POST'])
@login_required
def delete(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('주문이 삭제되었습니다.', 'success')
    return redirect(url_for('order.index'))

@bp.route('/place', methods=['POST'])
@login_required
@admin_required
def place_order():
    """발주 처리"""
    try:
        # POS 시스템과 재고 동기화
        success, error = sync_pos_inventory()
        if not success:
            flash(f"❌ POS 시스템 동기화 실패: {error}", "error")
            return redirect(url_for('order.order_view'))

        item_id = int(request.form['item_id'])
        qty = int(request.form['quantity'])
        notes = request.form.get('notes', '')

        # 재고 차감 시도
        success = consume_inventory(item_id, qty)
        if not success:
            flash("❌ 재고가 부족하거나 품목이 없습니다.", "error")
            return redirect(url_for('order.order_view'))

        # 발주 생성
        order = Order(
            order_number=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=current_user.id,
            status='pending',
            notes=notes
        )
        db.session.add(order)

        # 발주 품목 추가
        item = InventoryItem.query.get(item_id)
        order_item = OrderItem(
            order=order,
            item_id=item_id,
            quantity=qty,
            unit_price=item.unit_price or 0,
            total_price=qty * (item.unit_price or 0)
        )
        db.session.add(order_item)

        db.session.commit()
        flash("✅ 발주 및 재고 차감이 완료되었습니다.", "success")
        return redirect(url_for('order.order_view'))

    except ValueError as e:
        flash(f"❌ 잘못된 입력값: {str(e)}", "error")
        return redirect(url_for('order.order_view'))
    except Exception as e:
        db.session.rollback()
        flash(f"❌ 발주 처리 중 오류가 발생했습니다: {str(e)}", "error")
        return redirect(url_for('order.order_view'))

@bp.route('/view')
@login_required
def order_view():
    """발주 목록 조회"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('order/order_list.html', orders=orders)

@bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_order(order_id):
    """발주 취소"""
    order = Order.query.get_or_404(order_id)
    if order.status != 'pending':
        flash("❌ 대기 중인 발주만 취소할 수 있습니다.", "error")
        return redirect(url_for('order.order_view'))

    try:
        order.status = 'cancelled'
        db.session.commit()
        flash("✅ 발주가 취소되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ 발주 취소 중 오류가 발생했습니다: {str(e)}", "error")

    return redirect(url_for('order.order_view'))

@bp.route('/<int:order_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_order(order_id):
    """발주 승인"""
    order = Order.query.get_or_404(order_id)
    if order.status != 'pending':
        flash("❌ 대기 중인 발주만 승인할 수 있습니다.", "error")
        return redirect(url_for('order.order_view'))

    try:
        order.status = 'approved'
        order.approved_at = datetime.utcnow()
        order.approved_by = current_user.id
        db.session.commit()
        flash("✅ 발주가 승인되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ 발주 승인 중 오류가 발생했습니다: {str(e)}", "error")

    return redirect(url_for('order.order_view'))

order_bp = Blueprint('order', __name__, url_prefix='/api/orders')

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

@order_bp.route('/', methods=['GET'])
@login_required
def list_orders():
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
        return jsonify([{
            'id': o.id,
            'user': o.user.username,
            'item': o.item.name,
            'supplier': o.supplier.name,
            'quantity': o.quantity,
            'unit_price': o.unit_price,
            'total_price': o.total_price,
            'status': o.status,
            'order_date': o.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'delivery_date': o.delivery_date.strftime('%Y-%m-%d %H:%M:%S') if o.delivery_date else None
        } for o in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """발주 상세 조회"""
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify({
            'id': order.id,
            'user': order.user.username,
            'item': order.item.name,
            'supplier': order.supplier.name,
            'quantity': order.quantity,
            'unit_price': order.unit_price,
            'total_price': order.total_price,
            'status': order.status,
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'delivery_date': order.delivery_date.strftime('%Y-%m-%d %H:%M:%S') if order.delivery_date else None,
            'notes': order.notes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/', methods=['POST'])
@login_required
def create_order():
    """발주 생성"""
    try:
        data = request.json
        
        # 데이터 유효성 검사
        error = validate_order_data(data)
        if error:
            return jsonify({'error': error}), 400
        
        # 재고 품목 존재 여부 확인
        item = InventoryItem.query.get_or_404(data['item_id'])
        
        # 공급업체 존재 여부 확인
        supplier = Supplier.query.get_or_404(data['supplier_id'])
        
        # 발주 생성
        order = Order(
            user_id=current_user.id,
            item_id=data['item_id'],
            supplier_id=data['supplier_id'],
            quantity=data['quantity'],
            unit_price=data['unit_price'],
            notes=data.get('notes')
        )
        
        # 총 가격 계산
        order.calculate_total()
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'message': '발주가 성공적으로 등록되었습니다.',
            'order_id': order.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/<int:order_id>', methods=['PUT'])
@login_required
def update_order(order_id):
    """발주 수정"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.json
        
        # 수정 가능한 필드 업데이트
        if data.get('quantity'):
            order.quantity = data['quantity']
        if data.get('unit_price'):
            order.unit_price = data['unit_price']
        if data.get('status'):
            order.update_status(data['status'])
        if data.get('notes'):
            order.notes = data['notes']
        if data.get('delivery_date'):
            order.delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d')
        
        # 총 가격 재계산
        order.calculate_total()
        
        db.session.commit()
        
        return jsonify({
            'message': '발주가 성공적으로 수정되었습니다.',
            'order_id': order.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/<int:order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    """발주 삭제"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # 이미 처리된 발주는 삭제 불가
        if order.status != '대기중':
            return jsonify({'error': '이미 처리된 발주는 삭제할 수 없습니다.'}), 400
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({
            'message': '발주가 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 