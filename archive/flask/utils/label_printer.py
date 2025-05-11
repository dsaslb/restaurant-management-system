import win32print
import win32api
import tempfile
import os
from typing import List, Optional, Dict
import logging
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)

class LabelPrinter:
    """라벨 프린터 연동 클래스"""
    
    def __init__(self, printer_name: Optional[str] = None):
        """
        Args:
            printer_name (Optional[str]): 프린터 이름
        """
        self.printer_name = printer_name or win32print.GetDefaultPrinter()
    
    def get_available_printers(self) -> List[str]:
        """
        사용 가능한 프린터 목록을 반환합니다.
        
        Returns:
            List[str]: 프린터 이름 목록
        """
        try:
            printers = []
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 1):
                printers.append(printer[2])
            return printers
            
        except Exception as e:
            logger.error(f"프린터 목록 조회 중 오류 발생: {str(e)}")
            raise
    
    def print_label(self, image_path: str, copies: int = 1) -> bool:
        """
        라벨을 인쇄합니다.
        
        Args:
            image_path (str): 라벨 이미지 경로
            copies (int): 인쇄 매수
            
        Returns:
            bool: 인쇄 성공 여부
        """
        try:
            # 이미지 로드 및 크기 조정
            image = Image.open(image_path)
            image = image.resize((400, 200))  # 라벨 크기에 맞게 조정
            
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                image.save(temp_path, 'PNG')
            
            # 프린터 설정
            printer_handle = win32print.OpenPrinter(self.printer_name)
            printer_info = win32print.GetPrinter(printer_handle, 2)
            
            # 인쇄 작업 시작
            job = win32print.StartDocPrinter(printer_handle, 1, ("라벨 인쇄", None, "RAW"))
            
            try:
                win32print.StartPagePrinter(printer_handle)
                
                # 이미지 데이터 읽기
                with open(temp_path, 'rb') as f:
                    data = f.read()
                
                # 인쇄
                for _ in range(copies):
                    win32print.WritePrinter(printer_handle, data)
                
                win32print.EndPagePrinter(printer_handle)
                
            finally:
                win32print.EndDocPrinter(printer_handle)
                win32print.ClosePrinter(printer_handle)
            
            # 임시 파일 삭제
            os.unlink(temp_path)
            
            logger.info(f"라벨 인쇄 완료: {image_path} ({copies}매)")
            return True
            
        except Exception as e:
            logger.error(f"라벨 인쇄 중 오류 발생: {str(e)}")
            return False
    
    def print_batch_labels(self, image_paths: List[str], copies: int = 1) -> Dict[str, bool]:
        """
        여러 라벨을 일괄 인쇄합니다.
        
        Args:
            image_paths (List[str]): 라벨 이미지 경로 목록
            copies (int): 각 라벨의 인쇄 매수
            
        Returns:
            Dict[str, bool]: 각 라벨의 인쇄 성공 여부
        """
        results = {}
        
        for image_path in image_paths:
            success = self.print_label(image_path, copies)
            results[image_path] = success
            
            if not success:
                logger.warning(f"라벨 인쇄 실패: {image_path}")
        
        return results
    
    def check_printer_status(self) -> Dict:
        """
        프린터 상태를 확인합니다.
        
        Returns:
            Dict: 프린터 상태 정보
        """
        try:
            printer_handle = win32print.OpenPrinter(self.printer_name)
            printer_info = win32print.GetPrinter(printer_handle, 2)
            
            status = {
                'name': self.printer_name,
                'status': printer_info['Status'],
                'attributes': printer_info['Attributes'],
                'is_online': bool(printer_info['Status'] == 0),
                'is_ready': bool(printer_info['Status'] == 0 and printer_info['Attributes'] & win32print.PRINTER_ATTRIBUTE_READY),
                'is_error': bool(printer_info['Status'] != 0),
                'error_message': self._get_printer_error_message(printer_info['Status'])
            }
            
            win32print.ClosePrinter(printer_handle)
            return status
            
        except Exception as e:
            logger.error(f"프린터 상태 확인 중 오류 발생: {str(e)}")
            raise
    
    def _get_printer_error_message(self, status: int) -> str:
        """
        프린터 상태 코드에 따른 에러 메시지를 반환합니다.
        
        Args:
            status (int): 프린터 상태 코드
            
        Returns:
            str: 에러 메시지
        """
        error_messages = {
            0: "정상",
            1: "일시 중지",
            2: "오류",
            3: "대기 중",
            4: "인쇄 중",
            5: "용지 부족",
            6: "토너 부족",
            7: "도어 열림",
            8: "용지 걸림",
            9: "오프라인"
        }
        
        return error_messages.get(status, "알 수 없는 상태") 