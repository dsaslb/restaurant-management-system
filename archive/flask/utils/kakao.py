def send_kakao_to_admin(store_id, message):
    """관리자에게 카카오 알림을 보내는 함수"""
    print(f"[관리자 알림] 매장 {store_id}:\n{message}")
 
def send_kakao_to_employee(employee_id, message):
    """직원에게 카카오 알림을 보내는 함수"""
    print(f"[직원 알림] 직원 {employee_id}:\n{message}")

def send_kakao_alert(user_id, message):
    """카카오톡 알림 전송
    
    Args:
        user_id (int): 사용자 ID
        message (str): 알림 메시지
    """
    print(f"[카카오톡 알림] 사용자 {user_id}:\n{message}") 