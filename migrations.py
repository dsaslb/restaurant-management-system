import os
import logging
from datetime import datetime
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'sqlite:///restaurant.db')
        self.engine = create_engine(self.db_url)
        self.alembic_cfg = Config('alembic.ini')
        self.alembic_cfg.set_main_option('sqlalchemy.url', self.db_url)
        
    def init_migrations(self):
        """마이그레이션 초기화"""
        try:
            if not os.path.exists('migrations'):
                command.init(self.alembic_cfg, 'migrations')
                logger.info("마이그레이션 디렉토리가 생성되었습니다.")
            else:
                logger.info("마이그레이션 디렉토리가 이미 존재합니다.")
        except Exception as e:
            logger.error(f"마이그레이션 초기화 중 오류 발생: {str(e)}")
            raise
            
    def create_migration(self, message):
        """새 마이그레이션 생성"""
        try:
            command.revision(self.alembic_cfg, message=message, autogenerate=True)
            logger.info(f"새 마이그레이션 '{message}'가 생성되었습니다.")
        except Exception as e:
            logger.error(f"마이그레이션 생성 중 오류 발생: {str(e)}")
            raise
            
    def upgrade(self, revision='head'):
        """마이그레이션 적용"""
        try:
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"마이그레이션이 {revision}까지 적용되었습니다.")
        except Exception as e:
            logger.error(f"마이그레이션 적용 중 오류 발생: {str(e)}")
            raise
            
    def downgrade(self, revision):
        """마이그레이션 롤백"""
        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"마이그레이션이 {revision}으로 롤백되었습니다.")
        except Exception as e:
            logger.error(f"마이그레이션 롤백 중 오류 발생: {str(e)}")
            raise
            
    def current_revision(self):
        """현재 마이그레이션 버전 확인"""
        try:
            with self.engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
                return current_rev
        except Exception as e:
            logger.error(f"현재 마이그레이션 버전 확인 중 오류 발생: {str(e)}")
            raise
            
    def history(self):
        """마이그레이션 히스토리 확인"""
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            return script.get_history()
        except Exception as e:
            logger.error(f"마이그레이션 히스토리 확인 중 오류 발생: {str(e)}")
            raise
            
    def check_pending(self):
        """보류 중인 마이그레이션 확인"""
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            current_rev = self.current_revision()
            head_rev = script.get_current_head()
            return current_rev != head_rev
        except Exception as e:
            logger.error(f"보류 중인 마이그레이션 확인 중 오류 발생: {str(e)}")
            raise
            
    def backup_before_migration(self):
        """마이그레이션 전 데이터베이스 백업"""
        try:
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')
            
            with self.engine.connect() as conn:
                with open(backup_file, 'w') as f:
                    for table in self.engine.table_names():
                        result = conn.execute(text(f'SELECT * FROM {table}'))
                        f.write(f'-- Table: {table}\n')
                        for row in result:
                            f.write(f'INSERT INTO {table} VALUES {row};\n')
                            
            logger.info(f"데이터베이스가 {backup_file}에 백업되었습니다.")
            return backup_file
        except Exception as e:
            logger.error(f"데이터베이스 백업 중 오류 발생: {str(e)}")
            raise

# 마이그레이션 관리자 인스턴스 생성
migration_manager = MigrationManager()

if __name__ == '__main__':
    # 마이그레이션 초기화
    migration_manager.init_migrations()
    
    # 보류 중인 마이그레이션이 있는지 확인
    if migration_manager.check_pending():
        # 데이터베이스 백업
        backup_file = migration_manager.backup_before_migration()
        logger.info(f"마이그레이션 전 백업이 생성되었습니다: {backup_file}")
        
        # 마이그레이션 적용
        migration_manager.upgrade()
        logger.info("마이그레이션이 성공적으로 적용되었습니다.")
    else:
        logger.info("보류 중인 마이그레이션이 없습니다.") 