import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, current_app
from functools import wraps

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed, password)

def generate_jwt_token(user_data: dict, expires_in_hours: int = 48) -> str:
    payload = {
        'id': str(user_data.get('id')),
        'email': user_data.get('email'),
        'role': user_data.get('role', 'student'),
        'full_name': user_data.get('full_name', ''),
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=expires_in_hours),
        'iat': datetime.datetime.now(datetime.timezone.utc)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def get_current_user_from_request():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    token = parts[1]
    return decode_jwt_token(token)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user_from_request()
        if not current_user:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user_from_request()
        if not current_user:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        if current_user.get('role') != 'admin':
            return jsonify({'error': 'Access denied. Admin authorization required.'}), 403
        return f(current_user, *args, **kwargs)
    return decorated
