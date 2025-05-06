from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from models import db, WorkFeedback, Schedule, User
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

feedback_bp = Blueprint('feedback', __name__)
logger = logging.getLogger(__name__)

@feedback_bp.route('/feedback/<int:schedule_id>', methods=['GET'])
@jwt_required()
def feedback_form(schedule_id):
    """피드백 작성 폼"""
    try:
        # 스케줄 정보 조회
        schedule = Schedule.query.get_or_404(schedule_id)
        
        # 현재 사용자가 해당 스케줄의 직원인지 확인
        current_user_id = get_jwt_identity()
        if schedule.user_id != current_user_id:
            flash('권한이 없습니다.', 'error')
            return redirect(url_for('main.index'))
            
        # 이미 피드백이 있는지 확인
        existing_feedback = WorkFeedback.query.filter_by(
            schedule_id=schedule_id
        ).first()
        
        if existing_feedback:
            flash('이미 피드백을 제출했습니다.', 'error')
            return redirect(url_for('main.index'))
            
        return render_template('feedback.html',
            schedule_id=schedule_id,
            schedule_date=schedule.date.strftime('%Y-%m-%d'),
            start_time=schedule.start_time.strftime('%H:%M'),
            end_time=schedule.end_time.strftime('%H:%M')
        )
        
    except Exception as e:
        logger.error(f"피드백 폼 조회 중 오류 발생: {str(e)}")
        flash('피드백 폼을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@feedback_bp.route('/feedback/submit', methods=['POST'])
@jwt_required()
def feedback_submit():
    """피드백 제출"""
    try:
        # 필수 필드 검증
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        schedule_id = request.form.get('schedule_id')
        
        if not all([schedule_id, rating]):
            flash('필수 항목을 모두 입력해주세요.', 'error')
            return redirect(url_for('feedback.feedback_form', schedule_id=schedule_id))
            
        # 스케줄 존재 확인
        schedule = Schedule.query.get_or_404(schedule_id)
        
        # 현재 사용자가 해당 스케줄의 직원인지 확인
        current_user_id = get_jwt_identity()
        if schedule.user_id != current_user_id:
            flash('권한이 없습니다.', 'error')
            return redirect(url_for('main.index'))
            
        # 이미 피드백이 있는지 확인
        existing_feedback = WorkFeedback.query.filter_by(
            schedule_id=schedule_id
        ).first()
        
        if existing_feedback:
            flash('이미 피드백을 제출했습니다.', 'error')
            return redirect(url_for('main.index'))
            
        # 피드백 생성
        feedback = WorkFeedback(
            schedule_id=schedule_id,
            rating=int(rating),
            comment=comment,
            submitted_at=datetime.utcnow()
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('피드백이 성공적으로 제출되었습니다. 감사합니다!', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        logger.error(f"피드백 제출 중 오류 발생: {str(e)}")
        flash('피드백 제출 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('feedback.feedback_form', schedule_id=schedule_id))

@feedback_bp.route('/api/feedback/list', methods=['GET'])
@jwt_required()
def get_feedback_list():
    """피드백 목록 조회"""
    try:
        current_user_id = get_jwt_identity()
        
        # 관리자 권한 확인
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': '권한이 없습니다.'
            }), 403
            
        feedbacks = WorkFeedback.query.order_by(WorkFeedback.submitted_at.desc()).all()
        result = [{
            'id': f.id,
            'schedule_id': f.schedule_id,
            'rating': f.rating,
            'comment': f.comment,
            'submitted_at': f.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        } for f in feedbacks]

        return jsonify({
            'status': 'success',
            'feedbacks': result
        })
        
    except Exception as e:
        logger.error(f"피드백 목록 조회 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'피드백 목록을 불러오는 중 오류가 발생했습니다: {str(e)}'
        }), 500 