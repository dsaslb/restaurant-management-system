import requests
from app import KAKAO_REST_API_KEY, KAKAO_TEMPLATE_ID

def send_kakao_notification(admin_id, message):
    """
    카카오 알림톡을 전송하는 함수
    
    Args:
        admin_id (int): 관리자 ID
        message (str): 전송할 메시지
    """
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {KAKAO_REST_API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    template_data = {
        "template_id": KAKAO_TEMPLATE_ID,
        "template_args": {
            "message": message
        }
    }
    
    data = {
        "template_object": str(template_data)
    }
    
    response = requests.post(url, headers=headers, data=data)
    return response.status_code == 200 