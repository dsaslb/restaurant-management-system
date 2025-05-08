from flask import Blueprint, request, jsonify, Response
from flask_login import login_required
from models import db, Supplier
from utils.decorators import admin_required
from typing import Dict, List, Union, Optional, Tuple
from datetime import datetime

supplier_bp = Blueprint('suppliers', __name__, url_prefix='/api/suppliers')

@supplier_bp.route('/', methods=['GET'])
@login_required
def list_suppliers() -> Tuple[Response, int]:
    """
    공급처 목록을 조회합니다.
    
    Returns:
        tuple: (JSON 응답, HTTP 상태 코드)
        - 성공 시: 공급처 목록과 200 상태 코드
        - 실패 시: 에러 메시지와 500 상태 코드
        
    Example Response:
        [
            {
                "id": 1,
                "name": "신선식품공급",
                "contact_type": "email",
                "contact_info": "fresh@example.com",
                "default_lead_days": 1,
                "created_at": "2024-03-20 10:00:00",
                "updated_at": "2024-03-20 10:00:00"
            }
        ]
    """
    try:
        suppliers = Supplier.query.order_by(Supplier.name).all()
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'contact_type': s.contact_type,
            'contact_info': s.contact_info,
            'default_lead_days': s.default_lead_days,
            'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else None,
            'updated_at': s.updated_at.strftime('%Y-%m-%d %H:%M:%S') if s.updated_at else None
        } for s in suppliers]), 200
    except Exception as e:
        return jsonify({
            'error': '공급처 목록을 불러오는 중 오류가 발생했습니다.',
            'detail': str(e)
        }), 500

@supplier_bp.route('/', methods=['POST'])
@login_required
@admin_required
def create_supplier() -> Tuple[Response, int]:
    """
    새로운 공급처를 등록합니다.
    
    Request Body:
        {
            "name": "공급처명 (필수)",
            "contact_type": "연락처 유형 (선택, 기본값: email)",
            "contact_info": "연락처 정보 (선택)",
            "default_lead_days": "기본 발주 소요일 (선택, 기본값: 1)"
        }
    
    Returns:
        tuple: (JSON 응답, HTTP 상태 코드)
        - 성공 시: 성공 메시지와 201 상태 코드
        - 실패 시: 에러 메시지와 적절한 상태 코드
        
    Example Response:
        {
            "message": "공급처가 성공적으로 등록되었습니다.",
            "supplier_id": 1
        }
    """
    try:
        data = request.get_json() or {}
        
        # 필수값 체크
        name = data.get('name')
        if not name:
            return jsonify({
                'error': '공급처명이 누락되었습니다.',
                'detail': '공급처명은 반드시 입력해야 합니다.'
            }), 400

        # 중복 체크
        if Supplier.query.filter_by(name=name).first():
            return jsonify({
                'error': '이미 등록된 공급처명입니다.',
                'detail': '다른 공급처명을 사용해주세요.'
            }), 400

        supplier = Supplier(
            name=name,
            contact_type=data.get('contact_type', 'email'),
            contact_info=data.get('contact_info', ''),
            default_lead_days=data.get('default_lead_days', 1)
        )
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'message': '공급처가 성공적으로 등록되었습니다.',
            'supplier_id': supplier.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '공급처 등록 중 오류가 발생했습니다.',
            'detail': str(e)
        }), 500

@supplier_bp.route('/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_supplier(id: int) -> Tuple[Response, int]:
    """
    기존 공급처 정보를 수정합니다.
    
    Parameters:
        id (int): 수정할 공급처의 ID
        
    Request Body:
        {
            "name": "새 공급처명 (선택)",
            "contact_type": "새 연락처 유형 (선택)",
            "contact_info": "새 연락처 정보 (선택)",
            "default_lead_days": "새 기본 발주 소요일 (선택)"
        }
    
    Returns:
        tuple: (JSON 응답, HTTP 상태 코드)
        - 성공 시: 성공 메시지와 200 상태 코드
        - 실패 시: 에러 메시지와 적절한 상태 코드
        
    Example Response:
        {
            "message": "공급처가 성공적으로 수정되었습니다."
        }
    """
    try:
        supplier = Supplier.query.get_or_404(id)
        data = request.get_json() or {}
        
        # 이름 변경 시 중복 체크
        if 'name' in data and data['name'] != supplier.name:
            if Supplier.query.filter_by(name=data['name']).first():
                return jsonify({
                    'error': '이미 등록된 공급처명입니다.',
                    'detail': '다른 공급처명을 사용해주세요.'
                }), 400
        
        # 변경 가능한 필드만 업데이트
        for field in ('name', 'contact_type', 'contact_info', 'default_lead_days'):
            if field in data:
                setattr(supplier, field, data[field])
        
        db.session.commit()
        return jsonify({'message': '공급처가 성공적으로 수정되었습니다.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '공급처 수정 중 오류가 발생했습니다.',
            'detail': str(e)
        }), 500

@supplier_bp.route('/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_supplier(id: int) -> Tuple[Response, int]:
    """
    공급처를 삭제합니다.
    
    Parameters:
        id (int): 삭제할 공급처의 ID
        
    Returns:
        tuple: (JSON 응답, HTTP 상태 코드)
        - 성공 시: 성공 메시지와 200 상태 코드
        - 실패 시: 에러 메시지와 적절한 상태 코드
        
    Example Response:
        {
            "message": "공급처가 성공적으로 삭제되었습니다."
        }
    """
    try:
        supplier = Supplier.query.get_or_404(id)
        
        # 발주 내역이 있는지 확인
        if supplier.orders:
            return jsonify({
                'error': '공급처를 삭제할 수 없습니다.',
                'detail': '이 공급처에 연결된 발주 내역이 있습니다. 발주 내역을 먼저 삭제해주세요.'
            }), 400
        
        db.session.delete(supplier)
        db.session.commit()
        return jsonify({'message': '공급처가 성공적으로 삭제되었습니다.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '공급처 삭제 중 오류가 발생했습니다.',
            'detail': str(e)
        }), 500 