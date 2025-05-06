from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, InventoryItem, Ingredient, OrderItem, StockItem, StockTransaction, StockUsageAlert, User, InventoryBatch, Order
from datetime import datetime, date, timedelta
from utils.alerts import send_alert
from utils.inventory_report import get_monthly_inventory_report
from utils.inventory import consume_stock
from utils.decorators import admin_required
from utils.inventory_stats import get_usage_statistics
from utils.excel_export import export_stock_usage_to_excel
from utils.kakao import send_kakao_to_admin
from utils.notification import send_notification
import logging
import os
from werkzeug.utils import secure_filename

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')
logger = logging.getLogger(__name__)

@inventory_bp.route('/')
@login_required
def index():
    """재고 목록 페이지"""
    ingredients = Ingredient.query.all()
    return render_template('inventory/index.html', ingredients=ingredients)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    """재고 항목 추가"""
    if request.method == 'POST':
        name = request.form.get('name')
        unit = request.form.get('unit')
        min_quantity = float(request.form.get('min_quantity', 0))
        current_quantity = float(request.form.get('current_quantity', 0))
        
        ingredient = Ingredient(
            name=name,
            unit=unit,
            min_quantity=min_quantity
        )
        db.session.add(ingredient)
        db.session.flush()
        
        # 초기 재고 등록
        if current_quantity > 0:
            stock_item = StockItem(
                ingredient_id=ingredient.id,
                quantity=current_quantity
            )
            db.session.add(stock_item)
            
            # 재고 변동 기록
            transaction = StockTransaction(
                ingredient_id=ingredient.id,
                quantity=current_quantity,
                transaction_type='입고',
                note='초기 재고 등록'
            )
            db.session.add(transaction)
        
        db.session.commit()
        flash('재고 항목이 추가되었습니다.', 'success')
        return redirect(url_for('inventory.index'))
    
    return render_template('inventory/add.html')

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    """재고 항목 수정"""
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'POST':
        ingredient.name = request.form.get('name')
        ingredient.unit = request.form.get('unit')
        ingredient.min_quantity = float(request.form.get('min_quantity', 0))
        
        db.session.commit()
        flash('재고 항목이 수정되었습니다.', 'success')
        return redirect(url_for('inventory.index'))
    
    return render_template('inventory/edit.html', ingredient=ingredient)

@inventory_bp.route('/transaction', methods=['POST'])
@login_required
@admin_required
def transaction():
    """재고 변동 처리"""
    ingredient_id = request.form.get('ingredient_id')
    quantity = float(request.form.get('quantity'))
    transaction_type = request.form.get('transaction_type')
    note = request.form.get('note', '')
    
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    stock_item = StockItem.query.filter_by(ingredient_id=ingredient_id).first()
    
    if not stock_item:
        stock_item = StockItem(ingredient_id=ingredient_id, quantity=0)
        db.session.add(stock_item)
    
    if transaction_type == '입고':
        stock_item.quantity += quantity
    else:  # 출고
        if stock_item.quantity < quantity:
            return jsonify({'status': 'error', 'message': '재고가 부족합니다.'}), 400
        stock_item.quantity -= quantity
    
    transaction = StockTransaction(
        ingredient_id=ingredient_id,
        quantity=quantity,
        transaction_type=transaction_type,
        note=note
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '재고가 업데이트되었습니다.',
        'current_quantity': stock_item.quantity
    })

@inventory_bp.route('/history')
@login_required
def history():
    """재고 변동 내역"""
    transactions = StockTransaction.query.order_by(StockTransaction.created_at.desc()).all()
    return render_template('inventory/history.html', transactions=transactions)

@inventory_bp.route('/low-stock')
@login_required
def low_stock():
    """부족 재고 목록"""
    low_stock_items = []
    ingredients = Ingredient.query.all()
    
    for ingredient in ingredients:
        stock_item = StockItem.query.filter_by(ingredient_id=ingredient.id).first()
        current_quantity = stock_item.quantity if stock_item else 0
        
        if current_quantity <= ingredient.min_quantity:
            low_stock_items.append({
                'ingredient': ingredient,
                'current_quantity': current_quantity
            })
    
    return render_template('inventory/low_stock.html', low_stock_items=low_stock_items)

@inventory_bp.route('/api/inventory/item', methods=['POST'])
def create_item():
    """품목 등록"""
    data = request.get_json()
    name = data.get('name')
    unit = data.get('unit')
    min_quantity = data.get('min_quantity', 0)

    if not all([name, unit]):
        return jsonify({'status': 'error', 'message': '필수 값이 누락되었습니다.'}), 400

    if InventoryItem.query.filter_by(name=name).first():
        return jsonify({'status': 'error', 'message': '이미 존재하는 품목입니다.'}), 400

    item = InventoryItem(name=name, unit=unit, min_quantity=min_quantity)
    db.session.add(item)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '품목 등록 완료', 'item': item.to_dict()})

@inventory_bp.route('/api/inventory/receive', methods=['POST'])
def receive_stock():
    """입고 처리"""
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')

    if not all([item_id, quantity]):
        return jsonify({'status': 'error', 'message': '필수 값이 누락되었습니다.'}), 400

    item = InventoryItem.query.get_or_404(item_id)
    item.quantity += float(quantity)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '입고 완료', 'item': item.to_dict()})

@inventory_bp.route('/api/inventory/consume', methods=['POST'])
def consume_stock_api():
    """차감 처리"""
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')

    if not all([item_id, quantity]):
        return jsonify({'status': 'error', 'message': '필수 값이 누락되었습니다.'}), 400

    item = InventoryItem.query.get_or_404(item_id)
    quantity = float(quantity)
    
    if item.quantity < quantity:
        return jsonify({'status': 'error', 'message': '재고 부족'}), 400

    item.quantity -= quantity
    db.session.commit()

    # 최소 수량 체크
    if item.quantity <= item.min_quantity:
        send_alert(f"재고 부족: {item.name} ({item.quantity}{item.unit})")

    return jsonify({'status': 'success', 'message': '재고 차감 완료', 'item': item.to_dict()})

@inventory_bp.route('/api/inventory/items', methods=['GET'])
def get_items():
    """품목 목록 조회"""
    items = InventoryItem.query.all()
    return jsonify({
        'status': 'success',
        'items': [item.to_dict() for item in items]
    }) 

@inventory_bp.route('/order', methods=['GET', 'POST'])
@login_required
@admin_required
def order():
    if request.method == 'POST':
        try:
            # 주문 생성
            order = Order(
                order_number=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id=current_user.id,
                status='pending'
            )
            db.session.add(order)
            
            # 주문 항목 처리
            total_amount = 0
            for key, value in request.form.items():
                if key.startswith('qty_') and int(value) > 0:
                    item_id = int(key.split('_')[1])
                    quantity = int(value)
                    
                    item = InventoryItem.query.get(item_id)
                    if item:
                        # 주문 항목 생성
                        order_item = OrderItem(
                            order=order,
                            item_id=item_id,
                            quantity=quantity,
                            unit_price=item.unit_price or 0,
                            total_price=quantity * (item.unit_price or 0)
                        )
                        db.session.add(order_item)
                        total_amount += order_item.total_price
            
            order.total_amount = total_amount
            db.session.commit()
            
            flash('발주가 성공적으로 등록되었습니다.', 'success')
            return redirect(url_for('inventory.orders'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'발주 등록 중 오류가 발생했습니다: {str(e)}', 'error')
            return redirect(url_for('inventory.order'))
    
    # GET 요청 처리
    items = InventoryItem.query.all()
    today = date.today()
    warning_threshold = today + timedelta(days=3)
    
    inventory_list = []
    for item in items:
        # 남은 수량이 있는 배치 중 가장 빠른 유통기한 찾기 (FIFO)
        batch = (
            InventoryBatch.query
            .filter(InventoryBatch.item_id == item.id)
            .filter((InventoryBatch.quantity - InventoryBatch.used_quantity) > 0)
            .order_by(InventoryBatch.expiration_date)
            .first()
        )
        
        expire_date = batch.expiration_date if batch else None
        expire_soon = bool(expire_date and expire_date <= warning_threshold)
        
        inventory_list.append({
            'item': item,
            'expire_date': expire_date,
            'expire_soon': expire_soon
        })
    
    return render_template('inventory/order.html', inventory_list=inventory_list)

@inventory_bp.route('/orders')
@login_required
@admin_required
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('inventory/orders.html', orders=orders)

@inventory_bp.route('/order/new', methods=['GET', 'POST'])
@login_required
def order_new():
    """발주 등록"""
    if not current_user.is_admin:
        flash('권한이 없습니다.', 'error')
        return redirect(url_for('main.index'))

    ingredients = Ingredient.query.all()
    if request.method == 'POST':
        try:
            ing_id = int(request.form['ingredient_id'])
            qty = float(request.form['quantity'])
            cost = float(request.form['cost_per_unit'])
            
            # 발주 품목 생성
            order = OrderItem(
                ingredient_id=ing_id,
                quantity=qty,
                cost_per_unit=cost,
                total_cost=qty * cost,
                status='pending'
            )
            db.session.add(order)
            db.session.commit()

            # --- 과발주(Over-stock) 경고 체크 ---
            # 현재 재고 조회
            stock = StockItem.query.filter_by(ingredient_id=order.ingredient_id).first()
            current_qty = stock.quantity if stock else 0
            # 최대 허용량
            ing = Ingredient.query.get(order.ingredient_id)
            if current_qty + order.quantity > ing.max_stock:
                msg = (
                    f"[과발주 경고]\n"
                    f"{ing.name} 재고({current_qty}{ing.unit}) + 주문량({order.quantity}{ing.unit})\n"
                    f"> 최대허용량({ing.max_stock}{ing.unit})\n"
                    "확인 부탁드립니다."
                )
                # 관리자 알림
                send_kakao_to_admin(current_user.store_id, msg)
            
            flash('발주가 등록되었습니다.', 'success')
            return redirect(url_for('inventory.order_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'발주 등록 중 오류가 발생했습니다: {str(e)}', 'error')
            
    return render_template('inventory/order_new.html', ingredients=ingredients)

@inventory_bp.route('/order/list')
@login_required
def order_list():
    """발주 목록"""
    if not current_user.is_admin:
        flash('권한이 없습니다.', 'error')
        return redirect(url_for('main.index'))

    status = request.args.get('status', '')
    query = OrderItem.query
    
    if status:
        query = query.filter_by(status=status)
        
    orders = query.order_by(OrderItem.created_at.desc()).all()
    return render_template('inventory/order_list.html', orders=orders, status=status)

@inventory_bp.route('/order/<int:order_id>/approve', methods=['POST'])
@login_required
def approve_order(order_id):
    """발주 승인"""
    if not current_user.is_admin:
        flash('권한이 없습니다.', 'error')
        return redirect(url_for('inventory.order_list'))
        
    order = OrderItem.query.get_or_404(order_id)
    if order.status != 'pending':
        flash('이미 처리된 발주입니다.', 'error')
        return redirect(url_for('inventory.order_list'))
        
    try:
        order.status = 'approved'
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash('발주가 승인되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'발주 승인 중 오류가 발생했습니다: {str(e)}', 'error')
        
    return redirect(url_for('inventory.order_list'))

@inventory_bp.route('/order/<int:order_id>/receive', methods=['POST'])
@login_required
def receive_order(order_id):
    """발주 입고 처리"""
    if not current_user.is_admin:
        flash('권한이 없습니다.', 'error')
        return redirect(url_for('inventory.order_list'))
        
    order = OrderItem.query.get_or_404(order_id)
    if order.status != 'approved':
        flash('승인된 발주만 입고할 수 있습니다.', 'error')
        return redirect(url_for('inventory.order_list'))
        
    try:
        # 재고 업데이트
        ingredient = order.ingredient
        ingredient.current_stock += order.quantity
        
        # 재고 거래 내역 기록
        transaction = StockTransaction(
            ingredient_id=ingredient.id,
            transaction_type='purchase',
            quantity=order.quantity,
            reference_id=order.id,
            created_by=current_user.id,
            notes=f'발주 입고: {order.quantity} {ingredient.unit}'
        )
        
        order.status = 'received'
        order.updated_at = datetime.utcnow()
        
        db.session.add(transaction)
        db.session.commit()
        flash('입고가 완료되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'입고 처리 중 오류가 발생했습니다: {str(e)}', 'error')
        
    return redirect(url_for('inventory.order_list'))

@inventory_bp.route('/stock/<int:ingredient_id>/deduct', methods=['POST'])
@login_required
def deduct_stock(ingredient_id):
    """재고 차감 처리"""
    if not current_user.is_admin:
        flash('권한이 없습니다.', 'error')
        return redirect(url_for('inventory.stock_list'))
        
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    quantity = float(request.form.get('quantity', 0))
    notes = request.form.get('notes', '')
    
    if quantity <= 0:
        flash('차감할 수량을 입력해주세요.', 'error')
        return redirect(url_for('inventory.stock_detail', ingredient_id=ingredient_id))
        
    if ingredient.current_stock < quantity:
        flash('현재 재고가 부족합니다.', 'error')
        return redirect(url_for('inventory.stock_detail', ingredient_id=ingredient_id))
        
    try:
        # 재고 업데이트
        ingredient.current_stock -= quantity
        
        # 거래 내역 기록
        transaction = StockTransaction(
            ingredient_id=ingredient.id,
            transaction_type='usage',
            quantity=-quantity,  # 음수로 기록
            created_by=current_user.id,
            notes=notes
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        flash('재고가 차감되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'재고 차감 중 오류가 발생했습니다: {str(e)}', 'error')
        
    return redirect(url_for('inventory.stock_detail', ingredient_id=ingredient_id))

@inventory_bp.route('/stock/batch-deduct', methods=['POST'])
@login_required
def batch_deduct_stock():
    """여러 재고 동시 차감"""
    if not current_user.is_admin:
        flash('권한이 없습니다.', 'error')
        return redirect(url_for('inventory.stock_list'))
        
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'error': '잘못된 요청입니다.'}), 400
            
        items = data['items']
        notes = data.get('notes', '')
        
        # 트랜잭션 시작
        db.session.begin_nested()
        
        for item in items:
            ingredient_id = item.get('ingredient_id')
            quantity = float(item.get('quantity', 0))
            
            if not ingredient_id or quantity <= 0:
                continue
                
            ingredient = Ingredient.query.get(ingredient_id)
            if not ingredient:
                continue
                
            if ingredient.current_stock < quantity:
                raise ValueError(f'{ingredient.name}의 재고가 부족합니다.')
                
            # 재고 업데이트
            ingredient.current_stock -= quantity
            
            # 거래 내역 기록
            transaction = StockTransaction(
                ingredient_id=ingredient.id,
                transaction_type='usage',
                quantity=-quantity,
                created_by=current_user.id,
                notes=notes
            )
            db.session.add(transaction)
            
        # 트랜잭션 커밋
        db.session.commit()
        return jsonify({'message': '재고가 차감되었습니다.'}), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'재고 차감 중 오류가 발생했습니다: {str(e)}'}), 500 

@inventory_bp.route('/report')
@login_required
def inventory_report():
    """월별 재고 리포트"""
    if not current_user.is_admin:
        flash('권한이 없습니다.', 'error')
        return redirect(url_for('inventory.index'))
        
    # 날짜 파라미터 처리
    today = date.today()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))
    
    # 리포트 데이터 조회
    report_data, start_date, end_date = get_monthly_inventory_report(year, month)
    
    return render_template('inventory/report.html',
                         report_data=report_data,
                         start_date=start_date,
                         end_date=end_date,
                         year=year,
                         month=month)

@inventory_bp.route('/stock/use', methods=['GET', 'POST'])
@login_required
@admin_required
def stock_use():
    """재고 사용 처리"""
    try:
        # GET 요청 처리
        if request.method == 'GET':
            ingredients = Ingredient.query.order_by(Ingredient.name).all()
            return render_template(
                'inventory/use_stock.html',
                ingredients=ingredients,
                title="재고 사용"
            )

        # POST 요청 처리
        try:
            ing_id = int(request.form.get('ingredient_id', 0))
            qty = float(request.form.get('quantity', 0))
            notes = request.form.get('notes', '').strip()
        except (ValueError, TypeError):
            flash('잘못된 입력값입니다.', 'error')
            return redirect(url_for('inventory.stock_use'))

        # 입력값 검증
        if ing_id <= 0 or qty <= 0:
            flash('유효하지 않은 수량입니다.', 'error')
            return redirect(url_for('inventory.stock_use'))

        # 재고 사용 처리
        try:
            consume_stock(
                ingredient_id=ing_id,
                quantity=qty,
                user_id=current_user.id,
                notes=notes
            )
            flash('재고가 성공적으로 차감되었습니다.', 'success')
            logger.info(f"재고 사용 완료: 사용자={current_user.id}, 식자재={ing_id}, 수량={qty}")
            return redirect(url_for('inventory.stock_list'))
            
        except ValueError as e:
            flash(str(e), 'error')
            logger.warning(f"재고 사용 실패: {str(e)}")
            return redirect(url_for('inventory.stock_use'))
            
    except Exception as e:
        logger.error(f"재고 사용 처리 중 오류 발생: {str(e)}")
        flash('처리 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('inventory.stock_use'))

@inventory_bp.route('/stock/usage-history')
@login_required
@admin_required
def stock_usage_history():
    """재고 사용 내역 조회"""
    try:
        # 필터 파라미터
        ingredient_id = request.args.get('ingredient_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 기본 쿼리
        query = StockTransaction.query.filter_by(transaction_type='usage')
        
        # 필터 적용
        if ingredient_id:
            query = query.filter_by(ingredient_id=ingredient_id)
        if start_date:
            query = query.filter(StockTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(StockTransaction.created_at <= end_date)
            
        # 정렬 및 페이지네이션
        page = request.args.get('page', 1, type=int)
        per_page = 20
        transactions = query.order_by(StockTransaction.created_at.desc())\
                          .paginate(page=page, per_page=per_page)
        
        # 식자재 목록 (필터용)
        ingredients = Ingredient.query.all()
        
        return render_template('inventory/usage_history.html',
                             transactions=transactions,
                             ingredients=ingredients,
                             current_ingredient_id=ingredient_id,
                             start_date=start_date,
                             end_date=end_date)
                             
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_list'))

@inventory_bp.route('/stock/usage-approval')
@login_required
@admin_required
def stock_usage_approval_list():
    """재고 사용 승인 대기 목록"""
    try:
        # 필터 파라미터
        status = request.args.get('status', 'pending')
        ingredient_id = request.args.get('ingredient_id', type=int)
        
        # 기본 쿼리
        query = StockTransaction.query.filter_by(transaction_type='usage')
        
        # 필터 적용
        if status:
            query = query.filter_by(status=status)
        if ingredient_id:
            query = query.filter_by(ingredient_id=ingredient_id)
            
        # 정렬 및 페이지네이션
        page = request.args.get('page', 1, type=int)
        per_page = 20
        transactions = query.order_by(StockTransaction.created_at.desc())\
                          .paginate(page=page, per_page=per_page)
        
        # 식자재 목록 (필터용)
        ingredients = Ingredient.query.all()
        
        return render_template('inventory/usage_approval.html',
                             transactions=transactions,
                             ingredients=ingredients,
                             current_status=status,
                             current_ingredient_id=ingredient_id)
                             
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_list'))

@inventory_bp.route('/stock/usage/<int:transaction_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_stock_usage(transaction_id):
    """재고 사용 승인"""
    try:
        transaction = StockTransaction.query.get_or_404(transaction_id)
        
        if transaction.status != 'pending':
            flash('이미 처리된 요청입니다.', 'error')
            return redirect(url_for('inventory.stock_usage_approval_list'))
            
        # 재고 차감
        ingredient = transaction.ingredient
        if ingredient.current_stock < abs(transaction.quantity):
            flash('재고가 부족합니다.', 'error')
            return redirect(url_for('inventory.stock_usage_approval_list'))
            
        ingredient.current_stock += transaction.quantity  # quantity는 이미 음수로 저장되어 있음
        
        # 승인 처리
        transaction.status = 'approved'
        transaction.approved_at = datetime.utcnow()
        transaction.approved_by = current_user.id
        
        db.session.commit()
        flash('재고 사용이 승인되었습니다.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        
    return redirect(url_for('inventory.stock_usage_approval_list'))

@inventory_bp.route('/stock/usage/<int:transaction_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_stock_usage(transaction_id):
    """재고 사용 거절"""
    try:
        transaction = StockTransaction.query.get_or_404(transaction_id)
        
        if transaction.status != 'pending':
            flash('이미 처리된 요청입니다.', 'error')
            return redirect(url_for('inventory.stock_usage_approval_list'))
            
        rejection_reason = request.form.get('rejection_reason', '')
        if not rejection_reason:
            flash('거절 사유를 입력해주세요.', 'error')
            return redirect(url_for('inventory.stock_usage_approval_list'))
            
        # 거절 처리
        transaction.status = 'rejected'
        transaction.approved_at = datetime.utcnow()
        transaction.approved_by = current_user.id
        transaction.rejection_reason = rejection_reason
        
        db.session.commit()
        flash('재고 사용이 거절되었습니다.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        
    return redirect(url_for('inventory.stock_usage_approval_list'))

@inventory_bp.route('/stock/usage-stats')
@login_required
@admin_required
def stock_usage_stats():
    """재고 사용 통계 대시보드"""
    try:
        # 날짜 필터
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 통계 데이터 조회
        stats = get_usage_statistics(start_date, end_date)
        if not stats:
            flash('통계 데이터를 불러오는데 실패했습니다.', 'error')
            return redirect(url_for('inventory.stock_list'))
            
        return render_template('inventory/usage_stats.html',
                             stats=stats,
                             start_date=start_date,
                             end_date=end_date)
                             
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_list'))

@inventory_bp.route('/stock/usage-history/export')
@login_required
@admin_required
def export_stock_usage():
    """재고 사용 내역 엑셀 다운로드"""
    try:
        # 필터 파라미터
        ingredient_id = request.args.get('ingredient_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 기본 쿼리
        query = StockTransaction.query.filter_by(transaction_type='usage')
        
        # 필터 적용
        if ingredient_id:
            query = query.filter_by(ingredient_id=ingredient_id)
        if start_date:
            query = query.filter(StockTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(StockTransaction.created_at <= end_date)
            
        # 데이터 조회
        transactions = query.order_by(StockTransaction.created_at.desc()).all()
        
        # 엑셀 파일 생성
        excel_file = export_stock_usage_to_excel(transactions)
        if not excel_file:
            flash('엑셀 파일 생성에 실패했습니다.', 'error')
            return redirect(url_for('inventory.stock_usage_history'))
            
        # 파일명 생성
        filename = f'재고사용내역_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_usage_history'))

@inventory_bp.route('/stock/usage-alerts')
@login_required
@admin_required
def stock_usage_alerts():
    """재고 사용 알림 설정 목록"""
    try:
        alerts = StockUsageAlert.query.all()
        ingredients = Ingredient.query.all()
        return render_template('inventory/usage_alerts.html',
                             alerts=alerts,
                             ingredients=ingredients)
                             
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_list'))

@inventory_bp.route('/stock/usage-alerts/add', methods=['POST'])
@login_required
@admin_required
def add_stock_usage_alert():
    """재고 사용 알림 설정 추가"""
    try:
        ingredient_id = int(request.form['ingredient_id'])
        threshold = float(request.form['threshold'])
        
        # 중복 체크
        if StockUsageAlert.query.filter_by(ingredient_id=ingredient_id).first():
            flash('이미 설정된 알림이 있습니다.', 'error')
            return redirect(url_for('inventory.stock_usage_alerts'))
            
        # 알림 설정 추가
        alert = StockUsageAlert(
            ingredient_id=ingredient_id,
            threshold=threshold
        )
        db.session.add(alert)
        db.session.commit()
        
        flash('알림 설정이 추가되었습니다.', 'success')
        return redirect(url_for('inventory.stock_usage_alerts'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_usage_alerts'))

@inventory_bp.route('/stock/usage-alerts/<int:alert_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_stock_usage_alert(alert_id):
    """재고 사용 알림 활성화/비활성화"""
    try:
        alert = StockUsageAlert.query.get_or_404(alert_id)
        alert.is_active = not alert.is_active
        db.session.commit()
        
        status = '활성화' if alert.is_active else '비활성화'
        flash(f'알림이 {status}되었습니다.', 'success')
        return redirect(url_for('inventory.stock_usage_alerts'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_usage_alerts'))

@inventory_bp.route('/stock/usage-alerts/<int:alert_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_stock_usage_alert(alert_id):
    """재고 사용 알림 설정 삭제"""
    try:
        alert = StockUsageAlert.query.get_or_404(alert_id)
        db.session.delete(alert)
        db.session.commit()
        
        flash('알림 설정이 삭제되었습니다.', 'success')
        return redirect(url_for('inventory.stock_usage_alerts'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('inventory.stock_usage_alerts'))

@inventory_bp.route('/items')
@login_required
def item_list():
    """재고 품목 목록"""
    items = InventoryItem.query.all()
    inventory_list = []
    
    for item in items:
        # 남은 수량이 있는 배치만 필터링하고 유통기한 순으로 정렬
        batches = InventoryBatch.query.filter_by(item_id=item.id)\
            .filter(InventoryBatch.quantity - InventoryBatch.used_quantity > 0)\
            .order_by(InventoryBatch.expiration_date).all()
        
        if batches:
            # 첫 번째 배치 정보 사용
            first_batch = batches[0]
            inventory_list.append({
                'item': item,
                'expire_date': first_batch.expiration_date,
                'expire_soon': first_batch.expire_soon,
                'available_quantity': first_batch.available_quantity
            })
    
    return render_template('inventory/items.html', inventory_list=inventory_list)

@inventory_bp.route('/order/<int:order_id>/view')
@login_required
@admin_required
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('inventory/view_order.html', order=order)

@inventory_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != 'pending':
        flash('대기 중인 발주만 취소할 수 있습니다.', 'error')
        return redirect(url_for('inventory.view_order', order_id=order.id))
    
    try:
        order.status = 'cancelled'
        db.session.commit()
        flash('발주가 취소되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'발주 취소 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(url_for('inventory.orders')) 