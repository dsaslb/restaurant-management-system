from flask import Blueprint, request, send_file, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.reporting import generate_sales_report
from utils.gpt_report import analyze_sales_data
from utils.decorators import admin_required
from datetime import date, datetime, timedelta

report_bp = Blueprint('report', __name__, url_prefix='/admin')

@report_bp.route('/report/pdf')
@login_required
@admin_required
def report_pdf():
    """판매 보고서 PDF 다운로드"""
    try:
        # 파라미터
        freq = request.args.get('freq', 'monthly')
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
        
        # PDF 생성
        path = generate_sales_report(year, month, frequency=freq)
        
        # 파일명
        filename = f"sales_report_{freq}_{year}_{month if freq=='monthly' else 'week'}.pdf"
        
        return send_file(
            path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'보고서 생성 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('report.report_view'))

@report_bp.route('/report')
@login_required
@admin_required
def report_view():
    """보고서 생성 페이지"""
    try:
        # 현재 연도/월
        today = date.today()
        current_year = today.year
        current_month = today.month
        
        # 연도 목록 (최근 5년)
        years = list(range(current_year - 4, current_year + 1))
        
        # 월 목록
        months = list(range(1, 13))
        
        # GPT 분석 결과
        start_date = date(current_year, current_month, 1)
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        analysis = analyze_sales_data(start_date, end_date)
        
        return render_template('report/pdf_template.html',
                             years=years,
                             months=months,
                             current_year=current_year,
                             current_month=current_month,
                             analysis=analysis)
                             
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@report_bp.route('/report/analyze')
@login_required
@admin_required
def analyze_report():
    """GPT 분석 결과 조회"""
    try:
        # 파라미터
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
        
        # 날짜 범위 계산
        start_date = date(year, month, 1)
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        # GPT 분석
        analysis = analyze_sales_data(start_date, end_date)
        
        return render_template('report/analysis.html',
                             year=year,
                             month=month,
                             analysis=analysis)
                             
    except Exception as e:
        flash(f'분석 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('report.report_view')) 