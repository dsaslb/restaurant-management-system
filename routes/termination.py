from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Employee, Contract, TerminationDocument, Notification
from datetime import datetime, date
from utils.pdf import generate_termination_pdf
from utils.kakao import send_kakao_alert
from utils.decorators import admin_required
from sqlalchemy import and_, or_
import os
import logging

termination_bp = Blueprint('termination', __name__)
logger = logging.getLogger(__name__)

@termination_bp.route('/admin/termination/new/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def create_termination(employee_id):
    """퇴직/해고/계약해지 문서 작성"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        contract = Contract.query.filter(
            and_(
                Contract.employee_id == employee.id,
                Contract.end_date >= date.today()
            )
        ).order_by(Contract.created_at.desc()).first()

        if request.method == 'POST':
            # 폼 데이터 검증
            doc_type = request.form.get('doc_type')
            reason = request.form.get('reason')
            effective_date = date.fromisoformat(request.form.get('effective_date'))

            if not all([doc_type, reason, effective_date]):
                flash('모든 필드를 입력해주세요.', 'error')
                return redirect(url_for('termination.create_termination', employee_id=employee_id))

            # 문서 생성
            document = TerminationDocument(
                employee_id=employee.id,
                document_type=doc_type,
                reason=reason,
                effective_date=effective_date,
                created_by=current_user.id
            )
            db.session.add(document)
            db.session.flush()  # ID 생성을 위해 flush

            # PDF 생성
            pdf_dir = os.path.join('static', 'terminations')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_filename = f"termination_{document.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)

            if not generate_termination_pdf(document, pdf_path):
                raise Exception("PDF 생성에 실패했습니다.")

            document.pdf_path = pdf_path
            db.session.commit()

            # 알림 생성
            notification = Notification(
                recipient_id=employee.user_id,
                title=f"{document.document_type} 문서 생성",
                content=f"귀하의 {document.document_type} 문서가 생성되었습니다. 서명이 필요합니다.",
                notification_type="termination"
            )
            db.session.add(notification)
            db.session.commit()

            # 카카오톡 알림
            try:
                send_kakao_alert(
                    employee.user.phone,
                    f"[{document.document_type}] 문서가 생성되었습니다.\n"
                    f"효력 발생일: {document.effective_date.strftime('%Y-%m-%d')}\n"
                    f"로그인 후 서명해주세요."
                )
            except Exception as e:
                logger.error(f"카카오톡 알림 전송 실패: {str(e)}")

            flash('문서가 성공적으로 생성되었습니다.', 'success')
            return redirect(url_for('termination.termination_list'))

        return render_template(
            'termination/new.html',
            employee=employee,
            contract=contract
        )

    except Exception as e:
        logger.error(f"문서 작성 중 오류 발생: {str(e)}")
        flash('문서 작성 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('termination.termination_list'))

@termination_bp.route('/termination/sign/<int:doc_id>', methods=['GET', 'POST'])
@login_required
def sign_termination(doc_id):
    """퇴직/해고/계약해지 문서 서명"""
    try:
        document = TerminationDocument.query.get_or_404(doc_id)
        
        # 권한 확인
        if current_user.employee.id != document.employee_id:
            flash('접근 권한이 없습니다.', 'error')
            return redirect(url_for('main.index'))
            
        if request.method == 'POST':
            document.signed_by_employee = True
            document.employee_signed_at = datetime.now()
            db.session.commit()
            
            # 관리자에게 알림
            notification = Notification(
                recipient_id=document.created_by,
                title=f"{document.document_type} 서명 완료",
                content=f"{document.employee.name}님이 {document.document_type}에 서명했습니다.",
                notification_type="termination"
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('서명이 완료되었습니다.', 'success')
            return redirect(url_for('main.index'))
            
        return render_template(
            'termination/sign.html',
            document=document
        )
        
    except Exception as e:
        logger.error(f"문서 서명 중 오류 발생: {str(e)}")
        flash('서명 처리 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@termination_bp.route('/admin/termination/list')
@login_required
@admin_required
def termination_list():
    """퇴직/해고/계약해지 문서 목록"""
    try:
        # 검색 파라미터
        search = request.args.get('search', '')
        doc_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        # 기본 쿼리
        query = TerminationDocument.query
        
        # 검색 조건 적용
        if search:
            query = query.join(Employee).filter(
                or_(
                    Employee.name.ilike(f'%{search}%'),
                    Employee.phone.ilike(f'%{search}%')
                )
            )
            
        if doc_type:
            query = query.filter(TerminationDocument.document_type == doc_type)
            
        if status == 'signed':
            query = query.filter(TerminationDocument.signed_by_employee == True)
        elif status == 'unsigned':
            query = query.filter(TerminationDocument.signed_by_employee == False)
            
        # 정렬 및 조회
        documents = query.order_by(
            TerminationDocument.created_at.desc()
        ).all()
        
        return render_template(
            'termination/list.html',
            documents=documents,
            search=search,
            doc_type=doc_type,
            status=status
        )
        
    except Exception as e:
        logger.error(f"문서 목록 조회 중 오류 발생: {str(e)}")
        flash('문서 목록을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index')) 