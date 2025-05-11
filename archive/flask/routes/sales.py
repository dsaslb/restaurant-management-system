from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, MenuItem, RecipeItem, SalesRecord, Ingredient
from utils.inventory import consume_stock
from utils.decorators import admin_required
from datetime import datetime

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
def sales_new():
    """판매 등록"""
    try:
        menus = MenuItem.query.filter_by(is_active=True).all()
        if request.method == 'POST':
            menu_id = int(request.form['menu_id'])
            qty = int(request.form['quantity'])
            notes = request.form.get('notes', '')
            
            menu = MenuItem.query.get_or_404(menu_id)
            
            # 재고 차감: 레시피 따라
            recipe = RecipeItem.query.filter_by(menu_id=menu_id).all()
            for item in recipe:
                try:
                    consume_stock(
                        ingredient_id=item.ingredient_id,
                        quantity=item.quantity * qty,
                        user_id=current_user.id,
                        notes=f'메뉴 판매: {menu.name} {qty}개'
                    )
                except ValueError as e:
                    flash(f'재고 부족: {item.ingredient.name} - {str(e)}', 'error')
                    return redirect(url_for('sales.sales_new'))
            
            # 판매 기록 저장
            total = menu.price * qty
            record = SalesRecord(
                menu_id=menu_id,
                quantity=qty,
                total_price=total,
                created_by=current_user.id,
                notes=notes
            )
            db.session.add(record)
            db.session.commit()
            
            flash('판매가 등록되었습니다.', 'success')
            return redirect(url_for('sales.sales_list'))
            
        return render_template('sales/new.html', menus=menus)
        
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('sales.sales_list'))

@sales_bp.route('/list')
@login_required
def sales_list():
    """판매 내역 리스트"""
    try:
        # 필터 파라미터
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        menu_id = request.args.get('menu_id', type=int)
        
        # 기본 쿼리
        query = SalesRecord.query
        
        # 필터 적용
        if not current_user.is_admin:
            query = query.filter_by(created_by=current_user.id)
        if start_date:
            query = query.filter(SalesRecord.sold_at >= start_date)
        if end_date:
            query = query.filter(SalesRecord.sold_at <= end_date)
        if menu_id:
            query = query.filter_by(menu_id=menu_id)
            
        # 정렬 및 페이지네이션
        page = request.args.get('page', 1, type=int)
        per_page = 20
        records = query.order_by(SalesRecord.sold_at.desc())\
                      .paginate(page=page, per_page=per_page)
        
        # 메뉴 목록 (필터용)
        menus = MenuItem.query.all()
        
        return render_template('sales/list.html',
                             records=records,
                             menus=menus,
                             current_menu_id=menu_id,
                             start_date=start_date,
                             end_date=end_date)
                             
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@sales_bp.route('/stats')
@login_required
@admin_required
def sales_stats():
    """판매 통계"""
    try:
        # 날짜 필터
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 기본 쿼리
        query = SalesRecord.query
        
        # 필터 적용
        if start_date:
            query = query.filter(SalesRecord.sold_at >= start_date)
        if end_date:
            query = query.filter(SalesRecord.sold_at <= end_date)
            
        # 통계 데이터
        total_sales = query.with_entities(db.func.sum(SalesRecord.total_price)).scalar() or 0
        total_quantity = query.with_entities(db.func.sum(SalesRecord.quantity)).scalar() or 0
        
        # 메뉴별 판매량
        menu_sales = db.session.query(
            MenuItem.name,
            db.func.sum(SalesRecord.quantity).label('quantity'),
            db.func.sum(SalesRecord.total_price).label('total')
        ).join(SalesRecord)\
         .group_by(MenuItem.id)\
         .order_by(db.desc('total'))\
         .all()
        
        return render_template('sales/stats.html',
                             total_sales=total_sales,
                             total_quantity=total_quantity,
                             menu_sales=menu_sales,
                             start_date=start_date,
                             end_date=end_date)
                             
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('main.index')) 