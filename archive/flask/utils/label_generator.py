from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import qrcode
from pathlib import Path
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class LabelGenerator:
    """식품 라벨 생성기"""
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Args:
            template_path (Optional[str]): 라벨 템플릿 이미지 경로
        """
        self.template_path = template_path
        self.font_path = "static/fonts/NanumGothic.ttf"
        self.qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
    
    def generate_label(
        self,
        product_name: str,
        origin: str,
        expiration_date: datetime,
        storage: str,
        price: Optional[float] = None,
        barcode: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Image.Image:
        """
        식품 라벨을 생성합니다.
        
        Args:
            product_name (str): 제품명
            origin (str): 원산지
            expiration_date (datetime): 유통기한
            storage (str): 보관방법
            price (Optional[float]): 가격
            barcode (Optional[str]): 바코드
            output_path (Optional[str]): 저장 경로
        
        Returns:
            Image.Image: 생성된 라벨 이미지
        """
        try:
            # 기본 이미지 생성
            if self.template_path and Path(self.template_path).exists():
                img = Image.open(self.template_path)
            else:
                img = Image.new('RGB', (400, 200), color='white')
            
            draw = ImageDraw.Draw(img)
            
            # 폰트 설정
            title_font = ImageFont.truetype(self.font_path, 20)
            normal_font = ImageFont.truetype(self.font_path, 16)
            
            # 제품명
            draw.text((10, 10), f"제품명: {product_name}", font=title_font, fill='black')
            
            # 원산지
            draw.text((10, 40), f"원산지: {origin}", font=normal_font, fill='black')
            
            # 유통기한
            exp_date_str = expiration_date.strftime('%Y-%m-%d')
            draw.text((10, 70), f"유통기한: {exp_date_str}", font=normal_font, fill='black')
            
            # 보관방법
            draw.text((10, 100), f"보관방법: {storage}", font=normal_font, fill='black')
            
            # 가격
            if price:
                draw.text((10, 130), f"가격: {price:,}원", font=normal_font, fill='black')
            
            # QR 코드 생성
            qr_data = {
                'product_name': product_name,
                'origin': origin,
                'expiration_date': exp_date_str,
                'storage': storage
            }
            if price:
                qr_data['price'] = price
            if barcode:
                qr_data['barcode'] = barcode
            
            self.qr.clear()
            self.qr.add_data(str(qr_data))
            self.qr.make(fit=True)
            qr_img = self.qr.make_image(fill_color="black", back_color="white")
            
            # QR 코드 위치 조정
            qr_position = (img.width - qr_img.width - 10, 10)
            img.paste(qr_img, qr_position)
            
            # 바코드
            if barcode:
                draw.text((10, 160), f"바코드: {barcode}", font=normal_font, fill='black')
            
            # 저장
            if output_path:
                img.save(output_path)
                logger.info(f"라벨이 저장되었습니다: {output_path}")
            
            return img
            
        except Exception as e:
            logger.error(f"라벨 생성 중 오류 발생: {str(e)}")
            raise
    
    def generate_batch_labels(
        self,
        products: list,
        output_dir: str
    ) -> list:
        """
        여러 제품의 라벨을 일괄 생성합니다.
        
        Args:
            products (list): 제품 정보 리스트
            output_dir (str): 출력 디렉토리
        
        Returns:
            list: 생성된 라벨 파일 경로 리스트
        """
        output_paths = []
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        for i, product in enumerate(products):
            output_path = str(output_dir_path.joinpath(f"label_{i+1}.png"))
            self.generate_label(
                product_name=product['name'],
                origin=product['origin'],
                expiration_date=product['expiration_date'],
                storage=product['storage'],
                price=product.get('price'),
                barcode=product.get('barcode'),
                output_path=output_path
            )
            output_paths.append(output_path)
        
        return output_paths 