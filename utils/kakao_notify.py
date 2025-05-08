import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def send_kakao_notification(phone_number, message):
    """
    카카오 알림톡을 전송하는 함수
    
    Args:
        phone_number (str): 전송할 전화번호
        message (str): 전송할 메시지
        
    Returns:
        bool: 전송 성공 여부
    """
    # API 키 확인
    if not current_app.config.get('KAKAO_REST_API_KEY') or current_app.config['KAKAO_REST_API_KEY'] == 'your-kakao-rest-api-key':
        logger.warning("카카오 API 키가 설정되지 않았습니다. 알림톡이 전송되지 않습니다.")
        return False
        
    if not current_app.config.get('KAKAO_TEMPLATE_ID') or current_app.config['KAKAO_TEMPLATE_ID'] == 'your-kakao-template-id':
        logger.warning("카카오 템플릿 ID가 설정되지 않았습니다. 알림톡이 전송되지 않습니다.")
        return False

    try:
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {
            "Authorization": f"Bearer {current_app.config['KAKAO_REST_API_KEY']}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "template_id": current_app.config['KAKAO_TEMPLATE_ID'],
            "template_args": {
                "message": message
            }
        }
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            logger.error(f"카카오 알림톡 전송 실패: {response.text}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"카카오 알림톡 전송 중 오류 발생: {str(e)}")
        return False 