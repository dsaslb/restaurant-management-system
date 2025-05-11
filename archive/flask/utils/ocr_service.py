import re
from PIL import Image
import pytesseract
from datetime import datetime
import logging
from typing import Dict, Optional, Tuple, List
import cv2
import numpy as np
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class ProductInfo:
    """제품 정보 데이터 클래스"""
    name: str
    expiration_date: datetime.date
    origin: str
    storage: str
    confidence: float  # OCR 신뢰도 (0~1)
    raw_text: str     # 원본 텍스트
    origin_valid: bool = True  # 원산지 표기법 준수 여부
    origin_warning: Optional[str] = None  # 원산지 관련 경고 메시지

class OCRServiceError(Exception):
    """OCR 서비스 관련 예외"""
    pass

# 원산지 표기법 규칙
ORIGIN_RULES = {
    '육류': {
        'required': ['국가명', '도축장명'],
        'optional': ['도축일자'],
        'format': r'^[가-힣]+산\s*[가-힣]+(?:도|시|군|구)?\s*[가-힣]+(?:도축장|공장)?'
    },
    '수산물': {
        'required': ['국가명', '어획수역'],
        'optional': ['어획일자'],
        'format': r'^[가-힣]+산\s*[가-힣]+(?:해|바다|수역)?'
    },
    '농산물': {
        'required': ['국가명'],
        'optional': ['생산지'],
        'format': r'^[가-힣]+산(?:\s*[가-힣]+(?:도|시|군|구))?'
    },
    '가공식품': {
        'required': ['제조국'],
        'optional': ['제조사'],
        'format': r'^[가-힣]+제조(?:\s*[가-힣]+(?:제조사|공장))?'
    }
}

def validate_origin(product_type: str, origin: str) -> Tuple[bool, Optional[str]]:
    """
    원산지 표기법을 검증합니다.
    
    Args:
        product_type (str): 제품 유형 (육류, 수산물, 농산물, 가공식품)
        origin (str): 원산지 정보
    
    Returns:
        Tuple[bool, Optional[str]]: (유효성 여부, 경고 메시지)
    """
    if product_type not in ORIGIN_RULES:
        return False, f"지원하지 않는 제품 유형입니다: {product_type}"
    
    rule = ORIGIN_RULES[product_type]
    
    # 형식 검증
    if not re.match(rule['format'], origin):
        return False, f"원산지 표기 형식이 올바르지 않습니다. 예시: {rule['format']}"
    
    # 필수 항목 검증
    for required in rule['required']:
        if required not in origin:
            return False, f"필수 항목이 누락되었습니다: {required}"
    
    return True, None

def detect_product_type(name: str, origin: str) -> str:
    """
    제품 유형을 자동으로 감지합니다.
    
    Args:
        name (str): 제품명
        origin (str): 원산지 정보
    
    Returns:
        str: 제품 유형
    """
    # 제품명 기반 감지
    name = name.lower()
    if any(keyword in name for keyword in ['고기', '육', '돼지', '소', '닭']):
        return '육류'
    elif any(keyword in name for keyword in ['생선', '해산물', '어류', '새우']):
        return '수산물'
    elif any(keyword in name for keyword in ['채소', '과일', '곡물']):
        return '농산물'
    else:
        return '가공식품'

def preprocess_image(image_path: str) -> np.ndarray:
    """
    이미지 전처리를 수행합니다.
    
    Args:
        image_path (str): 이미지 파일 경로
    
    Returns:
        np.ndarray: 전처리된 이미지
    
    Raises:
        OCRServiceError: 이미지 처리 실패 시
    """
    try:
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise OCRServiceError(f"이미지를 로드할 수 없습니다: {image_path}")
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 대비 향상
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # 이진화
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
        
    except Exception as e:
        raise OCRServiceError(f"이미지 전처리 중 오류 발생: {str(e)}")

def extract_date(text: str) -> Optional[datetime.date]:
    """
    텍스트에서 날짜를 추출합니다.
    
    Args:
        text (str): 날짜가 포함된 텍스트
    
    Returns:
        Optional[datetime.date]: 추출된 날짜 또는 None
    """
    # 다양한 날짜 형식 패턴
    date_patterns = [
        r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})",  # YYYY-MM-DD
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",  # YYYY년 MM월 DD일
        r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})",  # YYYY. MM. DD
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                year, month, day = map(int, match.groups())
                return datetime(year, month, day).date()
            except ValueError:
                continue
    
    return None

def parse_product_image(image_path: str) -> ProductInfo:
    """
    이미지에서 제품 정보를 추출합니다.
    
    Args:
        image_path (str): 이미지 파일 경로
    
    Returns:
        ProductInfo: 추출된 제품 정보
    
    Raises:
        OCRServiceError: 이미지 처리 실패 시
    """
    try:
        # 이미지 전처리
        processed_image = preprocess_image(image_path)
        
        # OCR 수행
        custom_config = r'--oem 3 --psm 6 -l kor+eng'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # 신뢰도 점수 계산
        confidence = pytesseract.image_to_data(processed_image, config=custom_config, output_type=pytesseract.Output.DICT)
        avg_confidence = np.mean([float(conf) for conf in confidence['conf'] if conf != '-1']) / 100
        
        # 정보 추출
        info = {}
        
        # 제품명 추출
        name_patterns = [
            r"제품명[:\s]*([^\n]+)",
            r"상품명[:\s]*([^\n]+)",
            r"품목명[:\s]*([^\n]+)"
        ]
        for pattern in name_patterns:
            if match := re.search(pattern, text):
                info['name'] = match.group(1).strip()
                break
        
        # 유통기한 추출
        exp_patterns = [
            r"유통기한[:\s]*([^\n]+)",
            r"소비기한[:\s]*([^\n]+)",
            r"사용기한[:\s]*([^\n]+)"
        ]
        for pattern in exp_patterns:
            if match := re.search(pattern, text):
                date_text = match.group(1).strip()
                if date := extract_date(date_text):
                    info['expiration_date'] = date
                    break
        
        # 원산지 추출
        origin_patterns = [
            r"원산지[:\s]*([^\n]+)",
            r"제조국[:\s]*([^\n]+)",
            r"생산지[:\s]*([^\n]+)"
        ]
        for pattern in origin_patterns:
            if match := re.search(pattern, text):
                info['origin'] = match.group(1).strip()
                break
        
        # 보관방법 추출
        storage_patterns = [
            r"보관방법[:\s]*([^\n]+)",
            r"보관법[:\s]*([^\n]+)",
            r"보관[:\s]*([^\n]+)"
        ]
        for pattern in storage_patterns:
            if match := re.search(pattern, text):
                info['storage'] = match.group(1).strip()
                break
        
        # 필수 정보 검증
        if not info.get('name'):
            raise OCRServiceError("제품명을 추출할 수 없습니다.")
        if not info.get('expiration_date'):
            raise OCRServiceError("유통기한을 추출할 수 없습니다.")
        
        # 기본값 설정
        info.setdefault('origin', '미상')
        info.setdefault('storage', '상온보관')
        
        # 원산지 표기법 검증
        product_type = detect_product_type(info['name'], info['origin'])
        origin_valid, origin_warning = validate_origin(product_type, info['origin'])
        
        return ProductInfo(
            name=info['name'],
            expiration_date=info['expiration_date'],
            origin=info['origin'],
            storage=info['storage'],
            confidence=avg_confidence,
            raw_text=text,
            origin_valid=origin_valid,
            origin_warning=origin_warning
        )
        
    except Exception as e:
        logger.error(f"제품 정보 추출 중 오류 발생: {str(e)}")
        raise OCRServiceError(f"제품 정보 추출 실패: {str(e)}")

def validate_product_info(info: ProductInfo) -> Tuple[bool, Optional[str]]:
    """
    추출된 제품 정보의 유효성을 검증합니다.
    
    Args:
        info (ProductInfo): 검증할 제품 정보
    
    Returns:
        Tuple[bool, Optional[str]]: (유효성 여부, 오류 메시지)
    """
    try:
        # 제품명 검증
        if len(info.name) < 2:
            return False, "제품명이 너무 짧습니다."
        
        # 유통기한 검증
        if info.expiration_date < datetime.now().date():
            return False, "유통기한이 지났습니다."
        
        # 신뢰도 검증
        if info.confidence < 0.6:
            return False, "OCR 신뢰도가 낮습니다."
        
        return True, None
        
    except Exception as e:
        return False, f"검증 중 오류 발생: {str(e)}" 