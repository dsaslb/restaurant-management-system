from flask import Blueprint, jsonify
from models import db
from utils.response import api_response
from utils.logger import logger
import time
import os
import psutil

health_bp = Blueprint('health', __name__)

def check_database():
    """데이터베이스 연결 상태 확인"""
    try:
        db.session.execute('SELECT 1')
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

def check_disk_space():
    """디스크 공간 확인"""
    try:
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        return None

def check_memory_usage():
    """메모리 사용량 확인"""
    try:
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        }
    except Exception as e:
        logger.error(f"Memory usage check failed: {str(e)}")
        return None

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """시스템 상태 확인 API"""
    start_time = time.time()
    
    # 상태 정보 수집
    status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'uptime': time.time() - psutil.Process(os.getpid()).create_time(),
        'database': check_database(),
        'disk': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    # 전체 상태 확인
    if not status['database'] or not status['disk'] or not status['memory']:
        status['status'] = 'unhealthy'
    
    # 응답 시간 측정
    status['response_time'] = time.time() - start_time
    
    return api_response(
        data=status,
        message="시스템 상태 확인이 완료되었습니다.",
        status_code=200 if status['status'] == 'healthy' else 503
    )

@health_bp.route('/api/health/database', methods=['GET'])
def database_health():
    """데이터베이스 상태 확인 API"""
    is_healthy = check_database()
    return api_response(
        data={'healthy': is_healthy},
        message="데이터베이스 상태 확인이 완료되었습니다.",
        status_code=200 if is_healthy else 503
    )

@health_bp.route('/api/health/resources', methods=['GET'])
def resources_health():
    """시스템 리소스 상태 확인 API"""
    status = {
        'disk': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    is_healthy = all(status.values())
    return api_response(
        data=status,
        message="시스템 리소스 상태 확인이 완료되었습니다.",
        status_code=200 if is_healthy else 503
    ) 