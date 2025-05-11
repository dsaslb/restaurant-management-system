from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, send_file, send_from_directory, current_app
from models import Contract, Employee, db, ContractRenewalLog, SignatureLog, User, ContractTemplate, Notification
from datetime import datetime, timedelta, date
from routes.auth import token_required
from utils.pdf import generate_contract_pdf
from utils.alerts import send_admin_alert, send_kakao_alert
from utils.error_handler import ValidationError, DatabaseError, NotFoundError
from utils.response import api_response
from utils.decorators import db_session_required, validate_input, log_request, admin_required
from utils.logger import logger
import os
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user
import logging
from typing import Dict, Any, Optional, cast

contract_bp = Blueprint('contracts', __name__)
logger = logging.getLogger(__name__)

@contract_bp.route('/contracts/new', methods=['GET', 'POST'])
@token_required
def create_contract(user_id):
    if request.method == 'POST':
        try:
            data = request.form
            contract = Contract(
                employee_id=data.get('employee_id'),
                title=data.get('title'),
                content=data.get('content'),
                start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date(),
                signed=False
            )
            
            db.session.add(contract)
            db.session.commit()

            # 계약서 PDF 저장
            output_path = f'static/pdfs/contract_{contract.id}.pdf'
            contract.pdf_path = output_path
            generate_contract_pdf(contract, output_path)
            db.session.commit()

            flash('계약서가 등록되고 PDF가 저장되었습니다.')
            return redirect(url_for('contracts.list_contracts'))
        except Exception as e:
            flash('계약서 등록 실패')
            return jsonify({'status': 'error', 'message': str(e)}), 500

    employees = Employee.query.all()
    return render_template('contract_form.html', employees=employees)

@contract_bp.route('/contracts')
@token_required
def list_contracts(user_id):
    contracts = Contract.query.join(Employee).all()
    return render_template('contracts.html', contracts=contracts)

@contract_bp.route('/contracts/<int:contract_id>/sign', methods=['POST'])
@token_required
def sign_contract(user_id, contract_id):
    contract = Contract.query.get_or_404(contract_id)
    contract.signed = True
    contract.signed_at = datetime.now()
    db.session.commit()
    
    # 계약 만료 알림 설정
    check_contract_expiry()
    
    return jsonify({'status': 'success', 'message': '계약서에 서명 완료되었습니다.'})

def check_contract_expiry():
    """계약 만료일 자동 알림"""
    today = datetime.now().date()
    upcoming_contracts = Contract.query.filter(
        Contract.end_date <= today + timedelta(days=7),
        Contract.signed == True
    ).all()

    for contract in upcoming_contracts:
        days_left = (contract.end_date - today).days
        if days_left == 7 or days_left == 0:
            send_admin_alert(
                f"[알림] {contract.employee.name}님의 계약이 {days_left}일 후 만료됩니다."
            )

@contract_bp.route('/user/create', methods=['POST'], endpoint='user_create_contract')
@log_request
@validate_input(required_fields=['employee_id', 'start_date', 'end_date', 'salary', 'position'])
@db_session_required
def create_contract_user():
    """사용자 계약서 생성"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        salary = data.get('salary')
        position = data.get('position')

        # 직원 존재 확인
        employee = Employee.query.get(employee_id)
        if not employee:
            raise NotFoundError('직원을 찾을 수 없습니다.')

        # 계약서 생성
        contract = Contract(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            salary=salary,
            position=position
        )
        db.session.add(contract)
        db.session.commit()

        # PDF 생성
        try:
            pdf_dir = 'static/contracts'
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            pdf_path = os.path.join(pdf_dir, f'contract_{contract.id}.pdf')
            contract.generate_pdf(pdf_path)
            contract.pdf_path = pdf_path
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseError('PDF 생성 중 오류가 발생했습니다.')

        return api_response(contract.to_dict(), '계약서가 생성되었습니다.')

    except Exception as e:
        db.session.rollback()
        raise

@contract_bp.route('/admin/create', methods=['POST'], endpoint='admin_create_contract')
@log_request
@validate_input(required_fields=['employee_id', 'start_date', 'end_date', 'salary', 'position'])
@db_session_required
def create_contract_admin():
    """관리자 계약서 생성"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        salary = data.get('salary')
        position = data.get('position')

        # 직원 존재 확인
        employee = Employee.query.get(employee_id)
        if not employee:
            raise NotFoundError('직원을 찾을 수 없습니다.')

        # 계약서 생성
        contract = Contract(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            salary=salary,
            position=position
        )
        db.session.add(contract)
        db.session.commit()

        # PDF 생성
        try:
            pdf_dir = 'static/contracts'
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            pdf_path = os.path.join(pdf_dir, f'contract_{contract.id}.pdf')
            contract.generate_pdf(pdf_path)
            contract.pdf_path = pdf_path
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseError('PDF 생성 중 오류가 발생했습니다.')

        return api_response(contract.to_dict(), '계약서가 생성되었습니다.')

    except Exception as e:
        db.session.rollback()
        raise

@contract_bp.route('/<int:contract_id>', methods=['GET'], endpoint='get_contract')
@log_request
@db_session_required
def get_contract(contract_id):
    """계약서 조회"""
    contract = Contract.query.get_or_404(contract_id)
    return api_response(contract.to_dict())

@contract_bp.route('/<int:contract_id>/pdf', methods=['GET'], endpoint='download_contract_pdf')
@log_request
def download_contract_pdf(contract_id):
    """계약서 PDF 다운로드"""
    contract = Contract.query.get_or_404(contract_id)
    if not contract.pdf_path or not os.path.exists(contract.pdf_path):
        raise NotFoundError('PDF 파일을 찾을 수 없습니다.')
    return send_file(contract.pdf_path, as_attachment=True)

@contract_bp.route('/<int:contract_id>', methods=['PUT'], endpoint='update_contract')
@log_request
@validate_input(required_fields=['start_date', 'end_date', 'salary', 'position'])
@db_session_required
def update_contract(contract_id):
    """계약서 수정"""
    contract = Contract.query.get_or_404(contract_id)
    data = request.get_json()

    try:
        contract.start_date = data.get('start_date')
        contract.end_date = data.get('end_date')
        contract.salary = data.get('salary')
        contract.position = data.get('position')
        db.session.commit()

        # PDF 재생성
        if contract.pdf_path and os.path.exists(contract.pdf_path):
            os.remove(contract.pdf_path)
        pdf_dir = 'static/contracts'
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        pdf_path = os.path.join(pdf_dir, f'contract_{contract.id}.pdf')
        contract.generate_pdf(pdf_path)
        contract.pdf_path = pdf_path
        db.session.commit()

        return api_response(contract.to_dict(), '계약서가 수정되었습니다.')

    except Exception as e:
        db.session.rollback()
        raise DatabaseError('계약서 수정 중 오류가 발생했습니다.')

@contract_bp.route('/<int:contract_id>', methods=['DELETE'], endpoint='delete_contract')
@log_request
@db_session_required
def delete_contract(contract_id):
    """계약서 삭제"""
    contract = Contract.query.get_or_404(contract_id)
    
    try:
        # PDF 파일 삭제
        if contract.pdf_path and os.path.exists(contract.pdf_path):
            os.remove(contract.pdf_path)
        
        db.session.delete(contract)
        db.session.commit()
        return api_response(None, '계약서가 삭제되었습니다.')

    except Exception as e:
        db.session.rollback()
        raise DatabaseError('계약서 삭제 중 오류가 발생했습니다.')

@contract_bp.route('/api/contracts/renew', methods=['POST'])
def renew_contracts():
    data = request.get_json()
    extend_days = data.get('extend_days', 180)

    now = datetime.utcnow().date()
    expiring_contracts = Contract.query.filter(Contract.end_date <= now).all()

    for contract in expiring_contracts:
        old_end = contract.end_date
        contract.end_date = old_end + timedelta(days=extend_days)

        log = ContractRenewalLog(
            user_id=contract.user_id,
            old_end_date=old_end,
            new_end_date=contract.end_date
        )
        db.session.add(log)

    db.session.commit()
    return jsonify({'status': 'success', 'message': f'{len(expiring_contracts)}건 갱신 완료'})

@contract_bp.route('/api/contracts/renew_and_request_sign/<int:contract_id>', methods=['POST'])
def renew_and_request_signature(contract_id):
    """계약 갱신 및 서명 요청"""
    try:
        # 계약 조회
        contract = Contract.query.get_or_404(contract_id)
        
        # 갱신 일수 확인
        extend_days = request.json.get('extend_days', 180)
        if not isinstance(extend_days, int) or extend_days <= 0:
            return jsonify({
                'status': 'error',
                'message': '유효하지 않은 갱신 일수입니다.'
            }), 400
        
        # 기존 종료일 저장
        old_end_date = contract.end_date
        
        # 계약 갱신
        contract.end_date += timedelta(days=extend_days)
        contract.status = 'pending_signature'
        
        # 갱신 이력 기록
        renewal_log = ContractRenewalLog(
            user_id=contract.employee.user_id,
            old_end_date=old_end_date,
            new_end_date=contract.end_date
        )
        
        db.session.add(renewal_log)
        db.session.commit()
        
        # 서명 요청 알림 전송
        user = contract.employee.user
        if user.phone:
            try:
                send_kakao_alert(
                    user.phone,
                    f"[서명 요청] 새로운 계약서가 생성되었습니다.\n"
                    f"계약 기간: {old_end_date.strftime('%Y-%m-%d')} ~ {contract.end_date.strftime('%Y-%m-%d')}\n"
                    f"로그인 후 서명해주세요."
                )
            except Exception as e:
                logger.error(f"카카오톡 알림 전송 실패: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': '계약 갱신 및 서명 요청이 완료되었습니다.',
            'data': {
                'contract_id': contract.id,
                'old_end_date': old_end_date.isoformat(),
                'new_end_date': contract.end_date.isoformat(),
                'status': contract.status
            }
        })
        
    except Exception as e:
        logger.error(f"계약 갱신 중 오류 발생: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'계약 갱신 중 오류가 발생했습니다: {str(e)}'
        }), 500

@contract_bp.route('/api/contracts/sign/<int:contract_id>', methods=['POST'])
@jwt_required()
def sign_contract_jwt(contract_id):
    """계약서 서명"""
    try:
        # 현재 사용자 확인
        current_user_id = get_jwt_identity()
        
        # 계약서 존재 확인
        contract = Contract.query.get_or_404(contract_id)
        
        # 권한 확인 (직원만 자신의 계약서에 서명 가능)
        if contract.employee_id != current_user_id:
            return jsonify({
                'status': 'error',
                'message': '권한이 없습니다.'
            }), 403
            
        # 이미 서명된 계약서인지 확인
        existing_signature = SignatureLog.query.filter_by(
            contract_id=contract_id
        ).first()
        
        if existing_signature:
            return jsonify({
                'status': 'error',
                'message': '이미 서명된 계약서입니다.'
            }), 400
            
        # 서명 로그 생성
        log = SignatureLog(
            user_id=current_user_id,
            contract_id=contract_id,
            ip_address=request.remote_addr
        )
        
        # 계약서 상태 업데이트
        contract.status = 'signed'
        contract.updated_at = datetime.utcnow()
        
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"계약서 서명 완료: contract_id={contract_id}, user_id={current_user_id}")
        
        return jsonify({
            'status': 'success',
            'message': '계약서가 성공적으로 서명되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"계약서 서명 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'계약서 서명 중 오류가 발생했습니다: {str(e)}'
        }), 500

@contract_bp.route('/api/contracts/signature-logs/<int:contract_id>', methods=['GET'])
@jwt_required()
def get_signature_logs(contract_id):
    """계약서 서명 로그 조회"""
    try:
        # 현재 사용자 확인
        current_user_id = get_jwt_identity()
        
        # 계약서 존재 확인
        contract = Contract.query.get_or_404(contract_id)
        
        # 권한 확인 (관리자 또는 해당 계약서의 직원만 조회 가능)
        user = User.query.get(current_user_id)
        if not user.is_admin and contract.employee_id != current_user_id:
            return jsonify({
                'status': 'error',
                'message': '권한이 없습니다.'
            }), 403
            
        # 서명 로그 조회
        logs = SignatureLog.query.filter_by(
            contract_id=contract_id
        ).order_by(SignatureLog.signed_at.desc()).all()
        
        result = [{
            'id': log.id,
            'user_id': log.user_id,
            'signed_at': log.signed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': log.ip_address
        } for log in logs]
        
        return jsonify({
            'status': 'success',
            'logs': result
        })
        
    except Exception as e:
        logger.error(f"서명 로그 조회 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'서명 로그 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@contract_bp.route('/contracts/list')
@login_required
@admin_required
def contract_list():
    """계약 목록"""
    try:
        # 검색 파라미터
        search = request.args.get('search', '')
        store_id = request.args.get('store_id', type=int)
        
        # 계약 조회
        query = Contract.query.join(Employee).join(User)
        
        if search:
            query = query.filter(User.name.ilike(f'%{search}%'))
        if store_id:
            query = query.filter(Employee.store_id == store_id)
            
        contracts = query.order_by(Contract.end_date.desc()).all()
        
        return render_template(
            'contracts/contract_list.html',
            contracts=contracts,
            search=search,
            store_id=store_id,
            now=datetime.now().date()
        )
        
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@contract_bp.route('/contract/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def contract_page(employee_id):
    """계약서 페이지"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        contract = Contract.query.filter_by(employee_id=employee_id, signed=False).first()
        
        if not contract:
            # 새 계약서 자동 생성
            contract = Contract(
                employee_id=employee_id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
                pay_type='monthly',
                wage=employee.base_salary
            )
            db.session.add(contract)
            db.session.commit()
            
            logger.info(f'새 계약서 자동 생성: employee_id={employee_id}')
        
        return render_template(
            'contracts/contract_view.html',
            employee=employee,
            contract=contract
        )
    except Exception as e:
        logger.error(f'계약서 페이지 로드 중 오류 발생: {str(e)}')
        return render_template('error.html', message='계약서 처리 중 오류가 발생했습니다.'), 500

@contract_bp.route('/contract/complete')
@login_required
def contract_complete():
    """계약서 서명 완료 페이지"""
    return render_template('contracts/contract_complete.html')

@contract_bp.route('/api/contract/<int:contract_id>', methods=['PUT'])
@login_required
@validate_input(required_fields=['start_date', 'end_date', 'pay_type', 'wage'])
def update_contract_api(contract_id):
    """계약서 정보 업데이트"""
    try:
        if not current_user.is_admin:
            return api_response(
                {'message': '권한이 없습니다.'},
                status=403
            )

        data = request.get_json()
        contract = Contract.query.get_or_404(contract_id)
        
        contract.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        contract.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        contract.pay_type = data['pay_type']
        contract.wage = data['wage']
        contract.updated_at = datetime.now()
        
        # PDF 재생성
        if contract.pdf_path and os.path.exists(contract.pdf_path):
            os.remove(contract.pdf_path)
        pdf_dir = 'static/contracts'
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        pdf_path = os.path.join(pdf_dir, f'contract_{contract.id}.pdf')
        contract.generate_pdf(pdf_path)
        contract.pdf_path = pdf_path
        
        db.session.commit()
        logger.info(f'계약서 {contract_id} 업데이트 완료')
        
        return api_response(
            {'message': '계약서가 성공적으로 업데이트되었습니다.'}
        )
    except Exception as e:
        logger.error(f'계약서 업데이트 중 오류 발생: {str(e)}')
        db.session.rollback()
        return api_response(
            {'message': '계약서 업데이트 중 오류가 발생했습니다.'},
            status=500
        )

@contract_bp.route('/contracts/download/<path:filename>')
@login_required
def download_contract_pdf_file(filename):
    """계약서 PDF 다운로드"""
    try:
        directory = os.path.join(current_app.root_path, 'static/contracts')
        return send_from_directory(
            directory,
            filename,
            as_attachment=True
        )
    except Exception as e:
        logger.error(f'PDF 다운로드 중 오류 발생: {str(e)}')
        return api_response(
            {'message': 'PDF 파일을 찾을 수 없습니다.'},
            status=404
        )

@contract_bp.route('/templates')
@login_required
def template_list():
    """계약서 템플릿 목록 페이지"""
    if not current_user.is_admin:
        return render_template('error.html', message='접근 권한이 없습니다.'), 403
    return render_template('contracts/template_list.html')

@contract_bp.route('/api/templates', methods=['GET'])
@login_required
def get_templates():
    """계약서 템플릿 목록 조회"""
    try:
        if not current_user.is_admin:
            return api_response(
                {'message': '권한이 없습니다.'},
                status=403
            )

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')

        query = ContractTemplate.query

        if search:
            query = query.filter(
                db.or_(
                    ContractTemplate.title.ilike(f'%{search}%'),
                    ContractTemplate.content.ilike(f'%{search}%')
                )
            )

        if status:
            if status == 'active':
                query = query.filter_by(is_active=True)
            elif status == 'inactive':
                query = query.filter_by(is_active=False)

        templates = query.paginate(page=page, per_page=per_page)
        
        return api_response({
            'items': [template.to_dict() for template in templates.items],
            'total': templates.total,
            'pages': templates.pages,
            'current_page': templates.page
        })
    except Exception as e:
        logger.error(f'템플릿 목록 조회 중 오류 발생: {str(e)}')
        return api_response(
            {'message': '템플릿 목록 조회 중 오류가 발생했습니다.'},
            status=500
        )

@contract_bp.route('/api/templates', methods=['POST'])
@login_required
@validate_input(required_fields=['title', 'content'])
@db_session_required
def create_template():
    """계약서 템플릿 생성"""
    try:
        if not current_user.is_admin:
            return api_response(
                {'message': '권한이 없습니다.'},
                status=403
            )

        data = request.get_json()
        template = ContractTemplate(
            title=data['title'],
            content=data['content'],
            created_by=current_user.id
        )
        
        db.session.add(template)
        db.session.commit()
        logger.info(f'새 템플릿 생성: id={template.id}')
        
        return api_response(
            {'message': '템플릿이 성공적으로 생성되었습니다.'}
        )
    except Exception as e:
        logger.error(f'템플릿 생성 중 오류 발생: {str(e)}')
        return api_response(
            {'message': '템플릿 생성 중 오류가 발생했습니다.'},
            status=500
        )

@contract_bp.route('/api/templates/<int:template_id>', methods=['PUT'])
@login_required
@validate_input(required_fields=['title', 'content'])
@db_session_required
def update_template(template_id):
    """계약서 템플릿 수정"""
    try:
        if not current_user.is_admin:
            return api_response(
                {'message': '권한이 없습니다.'},
                status=403
            )

        data = request.get_json()
        template = ContractTemplate.query.get_or_404(template_id)
        
        template.title = data['title']
        template.content = data['content']
        template.updated_at = datetime.now()
        
        db.session.commit()
        logger.info(f'템플릿 {template_id} 업데이트 완료')
        
        return api_response(
            {'message': '템플릿이 성공적으로 업데이트되었습니다.'}
        )
    except Exception as e:
        logger.error(f'템플릿 업데이트 중 오류 발생: {str(e)}')
        return api_response(
            {'message': '템플릿 업데이트 중 오류가 발생했습니다.'},
            status=500
        )

@contract_bp.route('/api/templates/<int:template_id>', methods=['DELETE'])
@login_required
@db_session_required
def delete_template(template_id):
    """계약서 템플릿 삭제"""
    try:
        if not current_user.is_admin:
            return api_response(
                {'message': '권한이 없습니다.'},
                status=403
            )

        template = ContractTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        
        logger.info(f'템플릿 {template_id} 삭제 완료')
        
        return api_response(
            {'message': '템플릿이 성공적으로 삭제되었습니다.'}
        )
    except Exception as e:
        logger.error(f'템플릿 삭제 중 오류 발생: {str(e)}')
        return api_response(
            {'message': '템플릿 삭제 중 오류가 발생했습니다.'},
            status=500
        )

@contract_bp.route('/contracts/renew/<int:contract_id>', methods=['POST'])
@login_required
@admin_required
def renew_contract(contract_id):
    """계약 갱신"""
    try:
        old_contract = Contract.query.get_or_404(contract_id)
        employee = Employee.query.get(old_contract.employee_id)
        
        # 새 계약 생성
        new_contract = Contract(
            employee_id=old_contract.employee_id,
            start_date=old_contract.end_date + timedelta(days=1),
            end_date=old_contract.end_date + timedelta(days=365),
            pay_type=old_contract.pay_type,
            wage=old_contract.wage,
            pay_day=old_contract.pay_day,
            auto_renew=old_contract.auto_renew,
            signed=False,
            renewed_from_id=old_contract.id  # 갱신 이력 연결
        )
        
        # 갱신 로그 생성
        renewal_log = ContractRenewalLog(
            contract_id=old_contract.id,
            old_end_date=old_contract.end_date,
            new_end_date=new_contract.end_date,
            renewed_by=current_user.id
        )
        
        # 알림 생성
        notification = Notification(
            recipient_id=old_contract.employee.user_id,
            title="계약 갱신 알림",
            content=f"귀하의 계약이 {new_contract.end_date}까지 갱신되었습니다. 새로운 계약서에 서명해주세요.",
            notification_type="contract"
        )
        
        # PDF 생성
        pdf_dir = os.path.join('static', 'contracts')
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filename = f"contract_{new_contract.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        generate_contract_pdf(new_contract, pdf_path)
        new_contract.pdf_path = pdf_path
        
        db.session.add(new_contract)
        db.session.add(renewal_log)
        db.session.add(notification)
        db.session.commit()
        
        # 관리자에게 카카오톡 알림
        try:
            send_kakao_alert(
                current_user.phone,
                f"[계약 갱신] {employee.user.name}님의 신규 계약이 생성되었습니다.\n"
                f"계약 기간: {new_contract.start_date.strftime('%Y-%m-%d')} ~ {new_contract.end_date.strftime('%Y-%m-%d')}"
            )
        except Exception as e:
            logger.error(f"카카오톡 알림 전송 실패: {str(e)}")
        
        return redirect(url_for('contract.contract_page', employee_id=old_contract.employee_id))
        
    except Exception as e:
        db.session.rollback()
        return render_template('error.html', message=str(e)), 500 