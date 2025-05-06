import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from extensions import db
from models.pos import POSSaleLog, POSSaleItem, POSPerformanceLog
from models.inventory import InventoryItem
from utils.inventory import consume_inventory
from utils.kakao import send_kakao_to_admin
from config import Config
from tenacity import retry, stop_after_attempt, wait_exponential
import hmac
import hashlib
import json
from models import Inventory
from utils.notification import send_notification
import logging
logger = logging.getLogger(__name__)

class POSServiceError(Exception):
    """POS 서비스 관련 예외"""
    pass

def _is_pos_api_key_valid() -> bool:
    api_key = getattr(Config, 'POS_API_KEY', None)
    return bool(api_key and isinstance(api_key, str) and api_key.isascii())

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_recent_sales(minutes: int = 5) -> List[Dict]:
    """
    POS 서버에서 최근 판매 내역을 가져옵니다.
    
    Args:
        minutes (int): 몇 분 전까지의 판매 내역을 가져올지 (기본값: 5분)
    
    Returns:
        List[Dict]: 판매 내역 목록
    
    Raises:
        POSServiceError: API 호출 실패 시
    """
    if not _is_pos_api_key_valid():
        logger.warning("POS_API_KEY가 없거나 유효하지 않아 판매 내역을 가져오지 않습니다.")
        return []
    try:
        headers = {
            'Authorization': f'Bearer {Config.POS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'store_id': Config.POS_STORE_ID,
            'from': (datetime.now() - timedelta(minutes=minutes)).isoformat(),
            'to': datetime.now().isoformat()
        }
        
        response = requests.get(
            f"{Config.POS_API_URL}/sales/recent",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        return response.json().get('sales', [])
        
    except requests.exceptions.RequestException as e:
        error_msg = f"POS API 호출 실패: {str(e)}"
        logger.error(error_msg)
        raise POSServiceError(error_msg)

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    웹훅 서명을 검증합니다.
    
    Args:
        payload (bytes): 원본 페이로드
        signature (str): 서명
    
    Returns:
        bool: 검증 성공 여부
    """
    expected = hmac.new(
        Config.POS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

def handle_webhook(payload: bytes, signature: str) -> Tuple[bool, Optional[str]]:
    """
    POS 웹훅을 처리합니다.
    
    Args:
        payload (bytes): 웹훅 페이로드
        signature (str): 서명
    
    Returns:
        Tuple[bool, Optional[str]]: (성공 여부, 오류 메시지)
    """
    if not _is_pos_api_key_valid():
        logger.warning("POS_API_KEY가 없거나 유효하지 않아 웹훅 처리를 건너뜁니다.")
        return False, "POS_API_KEY가 설정되지 않았거나 유효하지 않습니다."
    try:
        if not verify_webhook_signature(payload, signature):
            return False, "잘못된 서명"
            
        data = json.loads(payload)
        event_type = data.get('type')
        
        if event_type == 'sale.created':
            return process_sale(data['sale'])
        elif event_type == 'sale.updated':
            # 판매 수정 처리
            sale_log = POSSaleLog.query.filter_by(sale_id=data['sale']['id']).first()
            if sale_log:
                sale_log.status = 'updated'
                db.session.commit()
            return True, None
        elif event_type == 'sale.cancelled':
            # 판매 취소 처리
            sale_log = POSSaleLog.query.filter_by(sale_id=data['sale']['id']).first()
            if sale_log:
                sale_log.status = 'cancelled'
                db.session.commit()
            return True, None
            
        return False, f"지원하지 않는 이벤트 타입: {event_type}"
        
    except Exception as e:
        error_msg = f"웹훅 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def process_sale(sale: Dict) -> Tuple[bool, Optional[str]]:
    """
    판매 내역을 처리하고 재고를 차감합니다.
    
    Args:
        sale (Dict): 판매 내역 데이터
    
    Returns:
        Tuple[bool, Optional[str]]: (성공 여부, 오류 메시지)
    """
    try:
        # 이미 처리된 판매인지 확인
        if POSSaleLog.query.filter_by(sale_id=sale['id']).first():
            return True, None
            
        # 판매 로그 생성
        sale_log = POSSaleLog(
            sale_id=sale['id'],
            pos_store_id=sale['store_id'],
            sale_date=datetime.fromisoformat(sale['sale_date']),
            total_amount=sale['total_amount'],
            discount_amount=sale.get('discount_amount', 0),
            payment_method=sale.get('payment_method')
        )
        db.session.add(sale_log)
        
        # 각 품목 처리
        success_items = []
        failed_items = []
        
        for item in sale['items']:
            try:
                # 품목 찾기
                inventory_item = InventoryItem.query.filter_by(
                    pos_item_id=item['id']
                ).first()
                
                if not inventory_item:
                    failed_items.append(f"품목을 찾을 수 없음: {item['name']}")
                    continue
                
                # 재고 차감
                if not consume_inventory(inventory_item.id, item['quantity']):
                    failed_items.append(f"재고 부족: {item['name']}")
                    continue
                
                # 판매 품목 기록
                sale_item = POSSaleItem(
                    sale=sale_log,
                    item_id=inventory_item.id,
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price'],
                    discount_price=item.get('discount_price', 0)
                )
                db.session.add(sale_item)
                success_items.append(item['name'])
                
            except Exception as e:
                failed_items.append(f"{item['name']}: {str(e)}")
        
        # 처리 결과 업데이트
        if failed_items:
            if success_items:
                sale_log.status = 'partial'
            else:
                sale_log.status = 'failed'
            sale_log.error_message = '\n'.join(failed_items)
            
            # 관리자에게 알림
            message = (
                f"POS 판매 처리 실패\n"
                f"판매번호: {sale['id']}\n"
                f"실패 항목:\n" + '\n'.join(failed_items)
            )
            send_kakao_to_admin(message)
        
        db.session.commit()
        return True, None
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"판매 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def log_performance(sync_start: datetime, success_count: int, fail_count: int, stats: Dict) -> None:
    """
    동기화 성능을 로깅합니다.
    
    Args:
        sync_start (datetime): 동기화 시작 시간
        success_count (int): 성공 건수
        fail_count (int): 실패 건수
        stats (Dict): 상세 통계
    """
    try:
        sync_end = datetime.now()
        total_sales = success_count + fail_count
        
        # 오류 요약 생성
        error_summary = {}
        if stats.get('error_types'):
            error_summary = {
                'total_errors': sum(stats['error_types'].values()),
                'error_types': stats['error_types']
            }
        
        # 성능 로그 생성
        performance_log = POSPerformanceLog(
            sync_start=sync_start,
            sync_end=sync_end,
            total_sales=total_sales,
            success_count=success_count,
            fail_count=fail_count,
            total_amount=stats.get('total_amount', 0),
            total_items=stats.get('total_items', 0),
            stats=json.dumps(stats),
            error_summary=json.dumps(error_summary)
        )
        
        db.session.add(performance_log)
        db.session.commit()
        
        # 성능 경고 체크
        if performance_log.duration > 60:  # 1분 이상 소요
            send_kakao_to_admin(
                f"POS 동기화 성능 경고\n"
                f"소요 시간: {performance_log.duration:.1f}초\n"
                f"처리 건수: {total_sales}건"
            )
            
    except Exception as e:
        logger.error(f"성능 로깅 중 오류 발생: {str(e)}")
        db.session.rollback()

def get_performance_report(days: int = 7) -> Dict:
    """
    성능 리포트를 생성합니다.
    
    Args:
        days (int): 조회 기간 (일)
    
    Returns:
        Dict: 성능 리포트
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        logs = (
            POSPerformanceLog.query
            .filter(POSPerformanceLog.sync_start >= start_date)
            .order_by(POSPerformanceLog.sync_start.desc())
            .all()
        )
        
        if not logs:
            return {
                'status': 'no_data',
                'message': '데이터가 없습니다.'
            }
        
        # 기본 통계
        total_syncs = len(logs)
        total_sales = sum(log.total_sales for log in logs)
        total_success = sum(log.success_count for log in logs)
        total_fail = sum(log.fail_count for log in logs)
        total_amount = sum(log.total_amount for log in logs)
        total_items = sum(log.total_items for log in logs)
        
        # 평균 처리 시간
        avg_duration = sum(log.duration for log in logs) / total_syncs
        
        # 성공률 추이
        success_rates = [log.success_rate for log in logs]
        avg_success_rate = sum(success_rates) / total_syncs
        
        # 결제 수단 통계
        payment_methods = {}
        for log in logs:
            stats = json.loads(log.stats)
            for method, count in stats.get('payment_methods', {}).items():
                payment_methods[method] = payment_methods.get(method, 0) + count
        
        # 오류 통계
        error_types = {}
        for log in logs:
            error_summary = json.loads(log.error_summary)
            for error_type, count in error_summary.get('error_types', {}).items():
                error_types[error_type] = error_types.get(error_type, 0) + count
        
        return {
            'status': 'success',
            'period': {
                'start': start_date.isoformat(),
                'end': datetime.now().isoformat()
            },
            'summary': {
                'total_syncs': total_syncs,
                'total_sales': total_sales,
                'total_success': total_success,
                'total_fail': total_fail,
                'total_amount': total_amount,
                'total_items': total_items,
                'avg_duration': avg_duration,
                'avg_success_rate': avg_success_rate
            },
            'payment_methods': payment_methods,
            'error_types': error_types,
            'daily_stats': [log.to_dict() for log in logs]
        }
        
    except Exception as e:
        logger.error(f"성능 리포트 생성 중 오류 발생: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

def sync_pos_sales() -> Tuple[bool, Optional[str]]:
    """
    POS 시스템의 판매 데이터를 동기화합니다.
    
    Returns:
        Tuple[bool, Optional[str]]: (성공 여부, 오류 메시지)
    """
    if not _is_pos_api_key_valid():
        logger.info("POS_API_KEY가 없거나 유효하지 않아 POS 동기화를 건너뜁니다.")
        return False, "POS_API_KEY가 설정되지 않았거나 유효하지 않습니다."

    try:
        headers = {"Authorization": f"Bearer {Config.POS_API_KEY}"}
        response = requests.get(
            f"{Config.POS_API_URL}/sales",
            headers=headers,
            params={"from": datetime.now() - timedelta(minutes=5)},
            timeout=5  # 타임아웃 설정
        )
        response.raise_for_status()
        sales_data = response.json()
        
        for sale in sales_data:
            for item in sale['items']:
                inventory = Inventory.query.filter_by(name=item['name']).first()
                if inventory:
                    success = consume_inventory(
                        inventory_id=inventory.id,
                        quantity=item['quantity']
                    )
                    if not success:
                        send_notification(
                            title="재고 차감 실패",
                            message=f"{item['name']} 재고 차감에 실패했습니다.",
                            level="error"
                        )
        return True, None
        
    except requests.exceptions.ConnectionError:
        logger.info("POS 서버에 연결할 수 없습니다. API 키가 설정되면 자동으로 동기화됩니다.")
        return False, "POS 서버에 연결할 수 없습니다."
    except requests.exceptions.Timeout:
        logger.info("POS 서버 응답 시간이 초과되었습니다.")
        return False, "POS 서버 응답 시간이 초과되었습니다."
    except requests.exceptions.RequestException as e:
        logger.info(f"POS API 호출 중 오류 발생: {str(e)}")
        return False, f"POS API 호출 중 오류 발생: {str(e)}"
    except Exception as e:
        logger.info(f"POS 동기화 중 오류 발생: {str(e)}")
        return False, f"POS 동기화 중 오류 발생: {str(e)}" 