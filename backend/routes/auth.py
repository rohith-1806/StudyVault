import re
from flask import Blueprint, request, jsonify, current_app
from utils.security import hash_password, verify_password, generate_jwt_token, login_required
from services.access_service import AccessService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not full_name:
        return jsonify({'error': 'Full name is required.'}), 400

    if not email or not re.match(EMAIL_REGEX, email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long.'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    db_service = current_app.config['DB_SERVICE']
    existing_user = db_service.get_profile_by_email(email)
    if existing_user:
        return jsonify({'error': 'An account with this email already exists.'}), 400

    pwd_hash = hash_password(password)
    user = db_service.create_user(full_name=full_name, email=email, password_hash=pwd_hash, role='student')

    token = generate_jwt_token(user)

    # Dispatch Welcome Email via Brevo with clear diagnostic tracking
    email_service = current_app.config.get('EMAIL_SERVICE')
    welcome_dispatched = False
    if email_service:
        if current_app.config.get('TESTING'):
            try:
                res = email_service.send_welcome_email(user)
                welcome_dispatched = res.get('success', False)
            except Exception as e:
                current_app.logger.warning(f"Welcome email test dispatch notice: {e}")
        else:
            if email_service.is_configured():
                current_app.logger.info("[Auth] User '%s' registered successfully. Dispatching welcome email job.", email)
                email_service.dispatch_async(email_service.send_welcome_email, user)
                welcome_dispatched = True
            else:
                current_app.logger.warning(
                    "[Auth] User '%s' registered successfully, but welcome email could not be sent: "
                    "BREVO_API_KEY or BREVO_SENDER_EMAIL is not configured in backend/.env.",
                    email
                )
                if db_service:
                    db_service.log_email(
                        user_id=user['id'],
                        email_type='welcome',
                        recipient=email,
                        reference_id=user['id'],
                        status='unconfigured',
                        error_message='Brevo API key or verified sender email is not configured in backend/.env.'
                    )

    if welcome_dispatched:
        success_msg = 'Account created successfully. Please check your email for the welcome message.'
    else:
        success_msg = 'Account created successfully.'

    return jsonify({
        'message': success_msg,
        'token': token,
        'user': {
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'role': user['role'],
            'avatar_url': user['avatar_url'],
            'access_active': AccessService.is_access_active(user),
            'access_expires_at': user.get('download_access_expires_at'),
            'created_at': user['created_at']
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    db_service = current_app.config['DB_SERVICE']
    user = db_service.get_profile_by_email(email)
    
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid email or password.'}), 401

    if not user.get('is_active', 1):
        return jsonify({'error': 'Your account has been disabled. Please contact support.'}), 403

    token = generate_jwt_token(user)

    return jsonify({
        'message': 'Login successful.',
        'token': token,
        'user': {
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'role': user['role'],
            'avatar_url': user['avatar_url'],
            'access_active': AccessService.is_access_active(user),
            'access_expires_at': user.get('download_access_expires_at'),
            'created_at': user['created_at']
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_me(current_user):
    db_service = current_app.config['DB_SERVICE']
    user = db_service.get_profile_by_id(current_user['id'])
    
    if not user:
        return jsonify({'error': 'User profile not found.'}), 404

    contributions = db_service.list_user_contributions(user['id'])
    approved_count = sum(1 for c in contributions if c.get('status') == 'approved')

    return jsonify({
        'user': {
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'role': user['role'],
            'avatar_url': user['avatar_url'],
            'is_active': bool(user.get('is_active', 1)),
            'access_active': AccessService.is_access_active(user),
            'remaining_seconds': AccessService.get_remaining_access_seconds(user),
            'access_started_at': user.get('download_access_started_at'),
            'access_expires_at': user.get('download_access_expires_at'),
            'total_uploads': len(contributions),
            'approved_uploads': approved_count,
            'created_at': user['created_at']
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Logged out successfully.'}), 200
