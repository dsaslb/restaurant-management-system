from datetime import datetime, timedelta
from models import Contract, ContractRenewalLog, Notification, db
from sqlalchemy import and_

def check_expiring_contracts(days=30):
    """만료 임박 계약 확인
    
    Args:
        days (int): 만료일 기준 일수 (기본값: 30일)
        
    Returns:
        list: 만료 임박 계약 목록
    """
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    return Contract.query.filter(
        and_(
            Contract.end_date <= end_date,
            Contract.end_date >= today
        )
    ).all()

def renew_contract(contract_id, new_end_date, renewed_by):
    """
    계약을 갱신하는 함수
    
    Args:
        contract_id (int): 갱신할 계약 ID
        new_end_date (date): 새로운 종료일
        renewed_by (int): 갱신한 관리자 ID
        
    Returns:
        Contract: 갱신된 계약 객체
    """
    try:
        # 기존 계약 조회
        old_contract = Contract.query.get_or_404(contract_id)
        
        # 새 계약 생성
        new_contract = Contract(
            employee_id=old_contract.employee_id,
            start_date=old_contract.end_date + timedelta(days=1),
            end_date=new_end_date,
            wage=old_contract.wage,
            pay_type=old_contract.pay_type,
            renewed_from_id=old_contract.id,
            renewed_by=renewed_by
        )
        
        db.session.add(new_contract)
        db.session.commit()
        
        return new_contract
        
    except Exception as e:
        db.session.rollback()
        raise e

def auto_renew_contracts():
    """자동 계약 갱신 처리"""
    try:
        # 만료 임박 계약 확인
        expiring_contracts = check_expiring_contracts(days=7)
        
        for contract in expiring_contracts:
            # 자동 갱신 조건 확인
            if contract.auto_renew and not contract.is_expired():
                # 1년 연장
                new_end_date = contract.end_date + timedelta(days=365)
                
                # 갱신 처리
                renew_contract(
                    contract_id=contract.id,
                    new_end_date=new_end_date,
                    renewed_by=1  # 시스템 계정 ID
                )
                
        return True
        
    except Exception as e:
        print(f"자동 계약 갱신 중 오류 발생: {str(e)}")
        return False 