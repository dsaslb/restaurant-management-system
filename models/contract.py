from datetime import datetime
from extensions import db

class Contract(db.Model):
    """계약 모델"""
    __tablename__ = 'contract'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    position = db.Column(db.String(50))
    salary = db.Column(db.Float)
    contract_type = db.Column(db.String(20))  # full-time, part-time, temporary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    employee = db.relationship('Employee', backref=db.backref('contracts', lazy=True))

    def __repr__(self):
        return f'<Contract {self.employee_id} - {self.contract_type}>'
    
    def to_dict(self):
        """계약 정보를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'position': self.position,
            'salary': self.salary,
            'contract_type': self.contract_type,
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