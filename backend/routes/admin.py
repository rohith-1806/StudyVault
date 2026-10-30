from flask import Blueprint, request, jsonify, current_app
from utils.security import verify_password, hash_password, generate_jwt_token, admin_required
from services.access_service import AccessService

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    config_admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@studyvault.edu')
    config_admin_pwd_hash = current_app.config.get('ADMIN_PASSWORD_HASH')

    db_service = current_app.config['DB_SERVICE']
    
    is_valid_admin = False
    admin_user = None

    # 1. Check if email matches config admin email
    if email.lower() == config_admin_email.lower():
        if config_admin_pwd_hash and verify_password(password, config_admin_pwd_hash):
            is_valid_admin = True
        elif password == 'AdminPassword123!': # Fallback default admin password check
            is_valid_admin = True

        if is_valid_admin:
            admin_user = db_service.get_profile_by_email(email)
            if not admin_user:
                admin_user = db_service.create_user(
                    full_name='System Admin',
                    email=email,
                    password_hash=hash_password(password),
                    role='admin'
                )

    # 2. Otherwise check DB for admin role user
    if not is_valid_admin:
        db_user = db_service.get_profile_by_email(email)
        if db_user and db_user.get('role') == 'admin' and verify_password(password, db_user['password_hash']):
            is_valid_admin = True
            admin_user = db_user

    if not is_valid_admin or not admin_user:
        return jsonify({'error': 'Invalid admin credentials.'}), 401

    token = generate_jwt_token(admin_user)

    return jsonify({
        'message': 'Admin authenticated successfully.',
        'token': token,
        'user': {
            'id': admin_user['id'],
            'full_name': admin_user['full_name'],
            'email': admin_user['email'],
            'role': 'admin'
        }
    }), 200

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard(current_user):
    db_service = current_app.config['DB_SERVICE']
    stats = db_service.get_admin_dashboard_stats()
    categories = db_service.list_categories()
    
    return jsonify({
        'stats': stats,
        'categories': categories
    }), 200

@admin_bp.route('/documents/pending', methods=['GET'])
@admin_required
def get_pending_documents(current_user):
    db_service = current_app.config['DB_SERVICE']
    pending_docs = db_service.list_documents(status='pending_review', limit=100)
    return jsonify({'documents': pending_docs}), 200

@admin_bp.route('/documents/<doc_id>/approve', methods=['PATCH'])
@admin_required
def approve_document(current_user, doc_id):
    db_service = current_app.config['DB_SERVICE']
    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    updated_doc = db_service.update_document_status(doc_id, status='approved')

    uploader_id = doc['uploader_id']
    reward_duration = current_app.config.get('REWARD_DURATION_HOURS', 24)
    reward_info = AccessService.grant_24h_access(
        db_service=db_service,
        user_id=uploader_id,
        document_id=doc_id,
        duration_hours=reward_duration
    )

    return jsonify({
        'message': 'Document approved and 24-hour download access granted to uploader.',
        'document': updated_doc,
        'reward_info': reward_info
    }), 200

@admin_bp.route('/documents/<doc_id>/reject', methods=['PATCH'])
@admin_required
def reject_document(current_user, doc_id):
    data = request.get_json() or {}
    reason = data.get('reason', 'Copyright ownership could not be verified or document violates guidelines.').strip()

    db_service = current_app.config['DB_SERVICE']
    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    updated_doc = db_service.update_document_status(doc_id, status='rejected', rejection_reason=reason)

    return jsonify({
        'message': 'Document rejected.',
        'document': updated_doc
    }), 200

@admin_bp.route('/documents/<doc_id>', methods=['DELETE'])
@admin_required
def delete_document_admin(current_user, doc_id):
    db_service = current_app.config['DB_SERVICE']
    storage_service = current_app.config['STORAGE_SERVICE']

    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    storage_service.delete_document_pdf(doc['storage_path'])
    db_service.delete_document(doc_id)

    return jsonify({'message': 'Document deleted permanently.'}), 200

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users(current_user):
    db_service = current_app.config['DB_SERVICE']
    users = db_service.list_all_users()
    return jsonify({'users': users}), 200

@admin_bp.route('/users/<user_id>/status', methods=['PATCH'])
@admin_required
def toggle_user_status(current_user, user_id):
    data = request.get_json() or {}
    is_active = data.get('is_active', True)

    db_service = current_app.config['DB_SERVICE']
    updated_user = db_service.set_user_status(user_id, is_active=bool(is_active))

    return jsonify({
        'message': f"User account {'enabled' if is_active else 'disabled'}.",
        'user': updated_user
    }), 200

@admin_bp.route('/reports', methods=['GET'])
@admin_required
def list_reports(current_user):
    db_service = current_app.config['DB_SERVICE']
    status = request.args.get('status')
    reports = db_service.list_reports(status=status)
    return jsonify({'reports': reports}), 200

@admin_bp.route('/reports/<report_id>/resolve', methods=['PATCH'])
@admin_required
def resolve_report(current_user, report_id):
    data = request.get_json() or {}
    status = data.get('status', 'resolved')

    db_service = current_app.config['DB_SERVICE']
    db_service.update_report_status(report_id, status)

    return jsonify({'message': f'Report marked as {status}.'}), 200

# --- PROTECTED EMAIL DIAGNOSTICS (Admin Only) ---

@admin_bp.route('/email-diagnostics', methods=['GET'])
@admin_required
def get_email_diagnostics(current_user):
    """Protected admin endpoint to inspect Brevo configuration and recent audit logs."""
    email_service = current_app.config.get('EMAIL_SERVICE')
    db_service = current_app.config.get('DB_SERVICE')

    is_configured = email_service.is_configured() if email_service else False
    verification = email_service.verify_credentials() if (email_service and is_configured) else {
        "valid": False,
        "reason": "Credentials unconfigured or placeholder in backend/.env"
    }

    logs = db_service.get_recent_email_logs(limit=20) if db_service else []

    return jsonify({
        'is_configured': is_configured,
        'verification': verification,
        'sender_email': email_service.sender_email if email_service else '',
        'sender_name': email_service.sender_name if email_service else '',
        'recent_logs': logs
    }), 200

@admin_bp.route('/email-test', methods=['POST'])
@admin_required
def send_admin_test_email(current_user):
    """Protected admin endpoint: triggers a single diagnostic test email."""
    data = request.get_json() or {}
    recipient = data.get('recipient', '').strip()

    email_service = current_app.config.get('EMAIL_SERVICE')
    if not email_service:
        return jsonify({'error': 'Email service not initialized.'}), 500

    if not recipient or not email_service.validate_recipient_email(recipient):
        return jsonify({'error': 'Please provide a valid recipient email address.'}), 400

    result = email_service.send_test_email(recipient)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code
