import os
import shutil
import logging
from datetime import datetime, timedelta
import sqlite3
import json
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, db_path: str, backup_dir: str = 'backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """백업 디렉토리 생성"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> str:
        """데이터베이스 백업 생성"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'db_backup_{timestamp}.db')
            
            # 데이터베이스 파일 복사
            shutil.copy2(self.db_path, backup_path)
            
            # 메타데이터 저장
            metadata = {
                'timestamp': timestamp,
                'size': os.path.getsize(backup_path),
                'path': backup_path
            }
            self._save_metadata(metadata)
            
            logger.info(f"백업 생성 완료: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"백업 생성 중 오류 발생: {str(e)}")
            raise

    def restore_backup(self, backup_path: str) -> bool:
        """백업에서 복구"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"백업 파일을 찾을 수 없습니다: {backup_path}")
            
            # 현재 데이터베이스 백업
            self.create_backup()
            
            # 백업 파일로 복구
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"복구 완료: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"복구 중 오류 발생: {str(e)}")
            return False

    def list_backups(self) -> List[Dict]:
        """백업 목록 조회"""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('db_backup_') and file.endswith('.db'):
                    path = os.path.join(self.backup_dir, file)
                    backups.append({
                        'path': path,
                        'timestamp': file.replace('db_backup_', '').replace('.db', ''),
                        'size': os.path.getsize(path)
                    })
            return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            logger.error(f"백업 목록 조회 중 오류 발생: {str(e)}")
            return []

    def _save_metadata(self, metadata: Dict):
        """백업 메타데이터 저장"""
        try:
            metadata_path = os.path.join(self.backup_dir, 'backup_metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    existing = json.load(f)
            else:
                existing = []
            
            existing.append(metadata)
            
            with open(metadata_path, 'w') as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            logger.error(f"메타데이터 저장 중 오류 발생: {str(e)}")

    def cleanup_old_backups(self, keep_days: int = 30):
        """오래된 백업 파일 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            for backup in self.list_backups():
                backup_date = datetime.strptime(backup['timestamp'], '%Y%m%d_%H%M%S')
                if backup_date < cutoff_date:
                    os.remove(backup['path'])
                    logger.info(f"오래된 백업 삭제: {backup['path']}")
        except Exception as e:
            logger.error(f"백업 정리 중 오류 발생: {str(e)}")

    def verify_backup(self, backup_path: str) -> bool:
        """백업 파일 검증"""
        try:
            # 데이터베이스 연결 시도
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # 테이블 존재 여부 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            conn.close()
            
            if not tables:
                return False
                
            return True
        except Exception as e:
            logger.error(f"백업 검증 중 오류 발생: {str(e)}")
            return False 