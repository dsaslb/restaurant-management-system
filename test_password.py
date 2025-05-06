from werkzeug.security import generate_password_hash, check_password_hash

# 비밀번호 해싱 테스트
def test_password():
    # 테스트할 비밀번호
    password = '1234'
    
    # 비밀번호 해싱
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
    print(f"해시된 비밀번호: {hashed_pw}")
    
    # 비밀번호 검증
    is_valid = check_password_hash(hashed_pw, password)
    print(f"올바른 비밀번호 검증: {is_valid}")
    
    # 잘못된 비밀번호 검증
    is_invalid = check_password_hash(hashed_pw, 'wrong_password')
    print(f"잘못된 비밀번호 검증: {is_invalid}")

if __name__ == '__main__':
    test_password() 