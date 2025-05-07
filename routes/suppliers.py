from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db, Supplier

supplier_bp = Blueprint('suppliers', __name__, url_prefix='/api/suppliers')

@supplier_bp.route('/', methods=['GET'])
# @login_required  # 테스트를 위해 임시로 제거
def list_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'contact': s.contact,
        'order_method': s.order_method,
        'default_lead_days': s.default_lead_days
    } for s in suppliers])

@supplier_bp.route('/', methods=['POST'])
@login_required
def create_supplier():
    data = request.get_json()
    s = Supplier(
        name=data['name'],
        contact=data.get('contact'),
        order_method=data.get('order_method', 'email'),
        default_lead_days=data.get('default_lead_days', 1)
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'message': '공급처 생성 완료', 'supplier_id': s.id}), 201

@supplier_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_supplier(id):
    s = Supplier.query.get_or_404(id)
    data = request.get_json()
    s.name = data.get('name', s.name)
    s.contact = data.get('contact', s.contact)
    s.order_method = data.get('order_method', s.order_method)
    s.default_lead_days = data.get('default_lead_days', s.default_lead_days)
    db.session.commit()
    return jsonify({'message': '공급처 수정 완료'})

@supplier_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_supplier(id):
    Supplier.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'message': '공급처 삭제 완료'}) 