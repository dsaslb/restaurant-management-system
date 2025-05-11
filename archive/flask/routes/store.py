from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Store
from utils.decorators import admin_required
import logging

store_bp = Blueprint('store', __name__)
logger = logging.getLogger(__name__)

@store_bp.route('/admin/stores')
@login_required
@admin_required
def store_list():
    """매장 목록 조회"""
    try:
        stores = Store.query.all()
        return render_template('admin/store_list.html', stores=stores)
    except Exception as e:
        logger.error(f"매장 목록 조회 중 오류 발생: {str(e)}")
        flash('매장 목록을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@store_bp.route('/admin/stores/<int:store_id>')
@login_required
@admin_required
def store_detail(store_id):
    """매장 상세 정보 조회"""
    try:
        store = Store.query.get_or_404(store_id)
        return render_template('admin/store_detail.html', store=store)
    except Exception as e:
        logger.error(f"매장 상세 정보 조회 중 오류 발생: {str(e)}")
        flash('매장 정보를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('store.store_list')) 