import requests
import json

BASE_URL = "http://localhost:5000"
TOKEN = None

def test_login():
    """관리자 로그인 테스트"""
    print("\n=== 관리자 로그인 테스트 ===")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin01", "password": "1234"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    global TOKEN
    if response.status_code == 200:
        TOKEN = response.json().get('token')
        return response.json().get('user', {}).get('id')
    return None

def test_employee_registration(admin_id):
    """직원 등록 테스트"""
    print("\n=== 직원 등록 테스트 ===")
    headers = {'Authorization': f'Bearer {TOKEN}'} if TOKEN else {}
    employee_data = {
        "name": "테스트직원",
        "username": "test_employee",
        "password": "1234",
        "role": "employee",
        "store_id": 1,
        "pay_type": "hourly",
        "wage": 9500
    }
    response = requests.post(
        f"{BASE_URL}/api/employees",
        json=employee_data,
        headers=headers
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get('id') if response.status_code == 200 else None

def test_contract_creation(user_id):
    """계약서 생성 테스트"""
    print("\n=== 계약서 생성 테스트 ===")
    headers = {'Authorization': f'Bearer {TOKEN}'} if TOKEN else {}
    contract_data = {
        "user_id": user_id,
        "start_date": "2025-05-01",
        "end_date": "2025-11-01",
        "pay_type": "hourly",
        "wage": 9500
    }
    response = requests.post(
        f"{BASE_URL}/api/contracts/create",
        json=contract_data,
        headers=headers
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_schedule_creation(user_id):
    """스케줄 등록 테스트"""
    print("\n=== 스케줄 등록 테스트 ===")
    headers = {'Authorization': f'Bearer {TOKEN}'} if TOKEN else {}
    schedule_data = {
        "user_id": user_id,
        "date": "2025-05-10",
        "start_time": "09:00",
        "end_time": "18:00"
    }
    response = requests.post(
        f"{BASE_URL}/api/schedule",
        json=schedule_data,
        headers=headers
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get('id') if response.status_code == 200 else None

def test_salary_calculation(user_id):
    """급여 계산 테스트"""
    print("\n=== 급여 계산 테스트 ===")
    headers = {'Authorization': f'Bearer {TOKEN}'} if TOKEN else {}
    salary_data = {
        "user_id": user_id,
        "start_date": "2025-05-01",
        "end_date": "2025-05-31"
    }
    response = requests.post(
        f"{BASE_URL}/api/salary/calculate",
        json=salary_data,
        headers=headers
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    # 1. 관리자 로그인
    admin_id = test_login()
    if not admin_id:
        print("로그인 실패. 테스트를 중단합니다.")
        exit(1)
    
    # 2. 직원 등록
    employee_id = test_employee_registration(admin_id)
    if not employee_id:
        print("직원 등록 실패. 테스트를 중단합니다.")
        exit(1)
    
    # 3. 계약서 생성
    test_contract_creation(employee_id)
    
    # 4. 스케줄 등록 및 확인
    schedule_id = test_schedule_creation(employee_id)
    
    # 5. 급여 계산
    test_salary_calculation(employee_id) 