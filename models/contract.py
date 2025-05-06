from datetime import datetime
from extensions import db
from models.employee import Employee, User

class Contract(db.Model):
    """계약 모델"""
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('contract_templates.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, expired, terminated
    pdf_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    employee = db.relationship('Employee', backref='contracts')
    template = db.relationship('ContractTemplate', backref='contracts')
    signatures = db.relationship('SignatureLog', backref='contract', lazy='dynamic')
    renewals = db.relationship('ContractRenewalLog', backref='contract', lazy='dynamic')
    
    def to_dict(self):
        """계약 정보를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'template_id': self.template_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'pdf_path': self.pdf_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def generate_pdf(self):
        """계약서 PDF 생성"""
        # TODO: PDF 생성 로직 구현
        pass

class ContractTemplate(db.Model):
    """계약서 템플릿 모델"""
    __tablename__ = 'contract_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SignatureLog(db.Model):
    """서명 로그 모델"""
    __tablename__ = 'signature_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    signature_type = db.Column(db.String(20), nullable=False)  # employee, manager, etc.
    signed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = db.relationship('User', backref='signatures')

class ContractRenewalLog(db.Model):
    """계약 갱신 로그 모델"""
    __tablename__ = 'contract_renewal_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    previous_end_date = db.Column(db.Date, nullable=False)
    new_end_date = db.Column(db.Date, nullable=False)
    renewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    renewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 관계 설정
    user = db.relationship('User', backref='contract_renewals') 