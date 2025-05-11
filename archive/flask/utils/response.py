from flask import jsonify
from typing import Any, Dict, Optional, Union

def api_response(
    status: Union[str, Dict[str, Any]] = 'success',
    message: Optional[str] = None,
    data: Optional[Union[Dict[str, Any], list, Any]] = None,
    status_code: int = 200
) -> tuple:
    """일관된 API 응답 형식 생성
    
    Args:
        status (Union[str, Dict[str, Any]]): 응답 상태 ('success' 또는 'error') 또는 상태 정보를 담은 딕셔너리
        message (str, optional): 응답 메시지
        data (Union[Dict[str, Any], list, Any], optional): 응답 데이터
        status_code (int): HTTP 상태 코드
        
    Returns:
        tuple: (jsonify된 응답, 상태 코드)
    """
    response = {
        'status': status
    }
    
    if message is not None:
        response['message'] = message
        
    if data is not None:
        response['data'] = data
        
    return jsonify(response), status_code 