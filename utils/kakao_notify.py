import requests
from flask import current_app

def send_kakao_notification(phone_number, message):
    """
    카카오 알림톡을 전송하는 함수
    
    Args:
        phone_number (str): 전송할 전화번호
        message (str): 전송할 메시지
    """
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
    return response.status_code == 200 