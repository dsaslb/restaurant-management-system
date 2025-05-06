from werkzeug.security import generate_password_hash

# 비밀번호 해싱
hashed = generate_password_hash("1234", method='pbkdf2:sha256')
print(hashed) 