from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from models import Employee, Contract, Attendance, Schedule, WorkEvaluation, Notification, TerminationDocument, db, NotificationSetting, NotificationLog
from utils.decorators import admin_required
from utils.statistics import get_attendance_stats, get_wage_stats, get_evaluation_stats
from utils.kakao import send_kakao_alert
from utils.pdf import generate_termination_pdf
from sqlalchemy import func, and_
from scheduler.low_stock_notifier import notify_low_stock
import logging
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/dashboard')
logger = logging.getLogger(__name__)

@admin_bp.route('/')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "접근 권한이 없습니다.", 403
    return render_template('admin/dashboard.html')

@admin_bp.route('/admin/contract_stats')
@login_required
@admin_required
def contract_stats():
    """계약 통계 대시보드"""
    try:
        # 기본 통계
        total = Contract.query.count()
        renewed = Contract.query.filter(Contract.renewed_from_id != None).count()
        expired = Contract.query.filter(Contract.end_date < date.today()).count()
        active = Contract.query.filter(Contract.end_date >= date.today()).count()
        
        # 최근 갱신된 계약
        recent_renewals = Contract.query.filter(
            Contract.renewed_from_id != None
        ).order_by(Contract.created_at.desc()).limit(5).all()
        
        # 만료 임박 계약
        expiring_soon = Contract.query.filter(
            Contract.end_date <= date.today() + timedelta(days=7),
            Contract.end_date >= date.today()
        ).all()
        
        return render_template(
            'admin/contract_stats.html',
            total=total,
            renewed=renewed,
            expired=expired,
            active=active,
            recent_renewals=recent_renewals,
            expiring_soon=expiring_soon
        )
        
    except Exception as e:
        logger.error(f"계약 통계 조회 중 오류 발생: {str(e)}")
        return render_template('error.html', message=str(e)), 500 

@admin_bp.route('/admin/termination', methods=['GET', 'POST'])
@login_required
@admin_required
def termination_documents():
    """퇴직/해고/계약해지 문서 관리"""
    try:
        if request.method == 'POST':
            data = request.form
            employee = Employee.query.get_or_404(data['employee_id'])
            
            # 문서 생성
            document = TerminationDocument(
                employee_id=employee.id,
                document_type=data['document_type'],
                reason=data['reason'],
                effective_date=datetime.strptime(data['effective_date'], '%Y-%m-%d').date(),
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
            return redirect(url_for('admin.termination_documents'))
        
        # 문서 목록 조회
        documents = TerminationDocument.query.order_by(
            TerminationDocument.created_at.desc()
        ).all()
        
        # 직원 목록 조회
        employees = Employee.query.all()
        
        return render_template(
            'admin/termination_documents.html',
            documents=documents,
            employees=employees
        )
        
    except Exception as e:
        logger.error(f"퇴직/해고/계약해지 문서 처리 중 오류 발생: {str(e)}")
        flash('문서 처리 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.termination_documents'))

@admin_bp.route('/admin/termination/new/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def new_termination_document(employee_id):
    """새 퇴직/해고/계약해지 문서 작성"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        if request.method == 'POST':
            data = request.form
            document = TerminationDocument(
                employee_id=employee_id,
                document_type=data['document_type'],
                reason=data['reason'],
                effective_date=datetime.strptime(data['effective_date'], '%Y-%m-%d').date(),
                created_by=current_user.id
            )
            
            # PDF 생성
            pdf_dir = os.path.join('static', 'terminations')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_filename = f"termination_{document.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            
            generate_termination_pdf(document, pdf_path)
            document.pdf_path = pdf_path
            
            db.session.add(document)
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
            
            return redirect(url_for('admin.termination_documents'))
        
        return render_template(
            'admin/new_termination.html',
            employee=employee
        )
        
    except Exception as e:
        logger.error(f"문서 작성 중 오류 발생: {str(e)}")
        return render_template('error.html', message=str(e)), 500

@admin_bp.route('/admin/termination/<int:doc_id>/sign', methods=['GET', 'POST'])
@login_required
@admin_required
def sign_termination_document(doc_id):
    """퇴직/해고/계약해지 문서 서명"""
    try:
        document = TerminationDocument.query.get_or_404(doc_id)
        
        if request.method == 'POST':
            document.signed_by_admin = True
            document.admin_signed_at = datetime.now()
            
            # PDF 재생성
            if document.pdf_path and os.path.exists(document.pdf_path):
                os.remove(document.pdf_path)
            
            pdf_dir = os.path.join('static', 'terminations')
            pdf_filename = f"termination_{document.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            
            if not generate_termination_pdf(document, pdf_path):
                raise Exception("PDF 재생성에 실패했습니다.")
            
            document.pdf_path = pdf_path
            db.session.commit()
            
            # 직원에게 알림
            notification = Notification(
                recipient_id=document.employee.user_id,
                title=f"{document.document_type} 문서 서명 완료",
                content=f"귀하의 {document.document_type} 문서에 관리자가 서명했습니다. 서명이 필요합니다.",
                notification_type="termination"
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('문서 서명이 완료되었습니다.', 'success')
            return redirect(url_for('admin.termination_documents'))
        
        return render_template(
            'admin/sign_termination.html',
            document=document
        )
        
    except Exception as e:
        logger.error(f"문서 서명 중 오류 발생: {str(e)}")
        flash('문서 서명 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.termination_documents'))

@admin_bp.route('/admin/notifications', methods=['GET', 'POST'])
@login_required
def notification_settings():
    if not current_user.is_admin:
        return "권한이 없습니다", 403

    setting = NotificationSetting.query.filter_by(name='low_stock').first()
    if not setting:
        setting = NotificationSetting(name='low_stock')
        db.session.add(setting)
        db.session.commit()

    if request.method == 'POST':
        setting.hour = int(request.form['hour'])
        setting.minute = int(request.form['minute'])
        db.session.commit()

        # 스케줄러 재등록
        sched = current_app.scheduler
        try:
            sched.remove_job('low_stock_notifier')
        except Exception:
            pass
        sched.add_job(
            notify_low_stock,
            'cron',
            hour=setting.hour,
            minute=setting.minute,
            id='low_stock_notifier'
        )
        return redirect(url_for('admin.notification_settings'))

    return render_template('admin/notification_settings.html', setting=setting)

@admin_bp.route('/admin/notification-logs')
@login_required
@admin_required
def notification_logs():
    """알림 로그 조회"""
    try:
        # 필터링 옵션
        notification_type = request.args.get('type')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 기본 쿼리
        query = NotificationLog.query
        
        # 필터 적용
        if notification_type:
            query = query.filter_by(notification_type=notification_type)
        if status:
            query = query.filter_by(status=status)
        if start_date:
            query = query.filter(NotificationLog.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(NotificationLog.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        # 정렬 및 페이지네이션
        page = request.args.get('page', 1, type=int)
        per_page = 20
        logs = query.order_by(NotificationLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 알림 유형 목록
        notification_types = db.session.query(
            NotificationLog.notification_type
        ).distinct().all()
        
        return render_template(
            'admin/notification_logs.html',
            logs=logs,
            notification_types=notification_types,
            current_type=notification_type,
            current_status=status,
            start_date=start_date,
            end_date=end_date
        )
        
    except Exception as e:
        logger.error(f"알림 로그 조회 중 오류 발생: {str(e)}")
        flash('알림 로그 조회 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.dashboard')) 