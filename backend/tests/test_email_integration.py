import os
import io
import pytest
import datetime
from app import create_app
from config import Config
from pypdf import PdfWriter
from services.db_service import DBService
from services.email_service import EmailService
from services.reminder_service import ReminderService
from services.access_service import AccessService

class EmailTestConfig(Config):
    TESTING = True
    AUTO_APPROVE = True
    SECRET_KEY = 'test-secret-key-studyvault-test-32bytes-min!'
    ADMIN_EMAIL = 'admin@studyvault.edu'
    ADMIN_PASSWORD_HASH = 'scrypt:32768:8:1$xH2g8l9B4v2k0L5m$95096b79753065a78248bc3bebb0ef3878b273b4b0e50efb0ef7645bfbc094208a0d0d82dd2604ca75a5cb33a6f1947b19818b76db01b1df40003b573510e140'
    BREVO_API_KEY = 'test-mock-api-key'
    BREVO_SENDER_EMAIL = 'verified-sender@studyvault.edu'
    BREVO_SENDER_NAME = 'StudyVault'
    FRONTEND_URL = 'http://localhost:5173'
    ENABLE_IN_APP_SCHEDULER = False

def create_valid_pdf_bytes(text="Educational test material for StudyVault digital library tests."):
    return (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj <</Length " + str(len(text) + 50).encode() + b">>\n"
        b"stream\nBT /F1 24 Tf 100 700 Td (" + text.encode() + b") Tj ET\nendstream\nendobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000236 00000 n\n0000000330 00000 n\n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n410\n%%EOF\n"
    )

@pytest.fixture
def test_setup(tmp_path):
    db_file = os.path.join(tmp_path, "email_test_database.db")
    app = create_app(EmailTestConfig)
    db_service = app.config['DB_SERVICE']
    db_service.db_path = db_file
    db_service._init_sqlite()

    sent_emails = []

    def mock_send(email_payload):
        sent_emails.append(email_payload)
        return {
            "success": True,
            "status": "sent",
            "message_id": f"mock-msg-{len(sent_emails)}"
        }

    email_service = app.config['EMAIL_SERVICE']
    email_service.set_mock_send_handler(mock_send)

    with app.test_client() as client:
        yield {
            "app": app,
            "client": client,
            "db_service": db_service,
            "email_service": email_service,
            "sent_emails": sent_emails,
            "db_file": db_file
        }

def register_user(client, email="student@univ.edu", name="Student One", password="Password123!"):
    return client.post('/api/auth/register', json={
        'full_name': name,
        'email': email,
        'password': password,
        'confirm_password': password
    })

def get_auth_token(client, email="student@univ.edu", name="Student One", password="Password123!"):
    res = register_user(client, email, name, password)
    return res.get_json()['token']

# ====================================================================
# 14 SPECIFIC TEST REQUIREMENTS
# ====================================================================

# 1. Successful registration sends one welcome email
def test_1_successful_registration_sends_one_welcome_email(test_setup):
    client = test_setup["client"]
    sent = test_setup["sent_emails"]

    res = register_user(client, email="alice@test.edu", name="Alice Wonderland")
    assert res.status_code == 201
    assert "token" in res.get_json()

    # Verify exactly 1 email sent to Alice with welcome subject and StudyVault branding
    welcome_emails = [e for e in sent if e["recipient_email"] == "alice@test.edu"]
    assert len(welcome_emails) == 1
    assert "Welcome to StudyVault" in welcome_emails[0]["subject"]
    assert "Team StudyVault" in welcome_emails[0]["text_content"]

# 2. Failed registration sends no welcome email
def test_2_failed_registration_sends_no_welcome_email(test_setup):
    client = test_setup["client"]
    sent = test_setup["sent_emails"]

    # Short password (< 8 chars)
    res = client.post('/api/auth/register', json={
        'full_name': 'Bad Password',
        'email': 'badpwd@test.edu',
        'password': 'short',
        'confirm_password': 'short'
    })
    assert res.status_code == 400

    # Mismatched passwords
    res = client.post('/api/auth/register', json={
        'full_name': 'Mismatch',
        'email': 'mismatch@test.edu',
        'password': 'Password123!',
        'confirm_password': 'DifferentPassword123!'
    })
    assert res.status_code == 400

    # Invalid email format
    res = client.post('/api/auth/register', json={
        'full_name': 'Invalid Email',
        'email': 'not-an-email',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    assert res.status_code == 400

    assert len(sent) == 0

# 3. Repeated registration requests do not send duplicate welcome emails
def test_3_repeated_registration_does_not_send_duplicate_welcome(test_setup):
    client = test_setup["client"]
    sent = test_setup["sent_emails"]

    # First registration
    res1 = register_user(client, email="duplicate_user@test.edu", name="First Try")
    assert res1.status_code == 201
    assert len([e for e in sent if e["recipient_email"] == "duplicate_user@test.edu"]) == 1

    # Second registration attempt with identical email
    res2 = register_user(client, email="duplicate_user@test.edu", name="Second Try")
    assert res2.status_code == 400
    assert "already exists" in res2.get_json()["error"]

    # Total welcome emails must still be exactly 1
    assert len([e for e in sent if e["recipient_email"] == "duplicate_user@test.edu"]) == 1

# 4. Valid resource upload grants the intended 24-hour access period
def test_4_valid_resource_upload_grants_24h_access(test_setup):
    client = test_setup["client"]
    db_service = test_setup["db_service"]

    token = get_auth_token(client, email="uploader@test.edu", name="Uploader Student")
    headers = {'Authorization': f'Bearer {token}'}

    # Before upload: access should be inactive
    user_before = db_service.get_profile_by_email("uploader@test.edu")
    assert AccessService.is_access_active(user_before) is False

    pdf_data = create_valid_pdf_bytes("Calculus 1 lecture notes for final exam preparation.")
    res = client.post('/api/documents/upload', headers=headers, data={
        'file': (io.BytesIO(pdf_data), 'Calculus_Notes.pdf'),
        'title': 'Calculus 1 Complete Lecture Notes',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    })
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["reward_granted"] is True
    assert json_data["reward_info"]["duration_hours"] == 24

    # Verify in database
    user_after = db_service.get_profile_by_email("uploader@test.edu")
    assert AccessService.is_access_active(user_after) is True
    assert AccessService.get_remaining_access_seconds(user_after) > 23 * 3600

# 5. Invalid uploads do not grant access
def test_5_invalid_upload_does_not_grant_access(test_setup):
    client = test_setup["client"]
    db_service = test_setup["db_service"]

    token = get_auth_token(client, email="invalid_uploader@test.edu")
    headers = {'Authorization': f'Bearer {token}'}

    # Attempt upload without copyright confirmation
    pdf_data = create_valid_pdf_bytes("Some notes")
    res = client.post('/api/documents/upload', headers=headers, data={
        'file': (io.BytesIO(pdf_data), 'notes.pdf'),
        'title': 'Unconfirmed Notes',
        'category_id': 'cat_1',
        'copyright_confirmed': 'false'
    })
    assert res.status_code == 400

    # User access must remain inactive
    user = db_service.get_profile_by_email("invalid_uploader@test.edu")
    assert AccessService.is_access_active(user) is False

# 6. Duplicate uploads do not incorrectly grant or reset access
def test_6_duplicate_uploads_do_not_grant_or_reset_access(test_setup):
    client = test_setup["client"]
    db_service = test_setup["db_service"]

    token1 = get_auth_token(client, email="user_one@test.edu")
    headers1 = {'Authorization': f'Bearer {token1}'}

    pdf_bytes = create_valid_pdf_bytes("Unique Physics thermodynamics notes content.")

    # First upload passes
    res1 = client.post('/api/documents/upload', headers=headers1, data={
        'file': (io.BytesIO(pdf_bytes), 'Physics_Notes.pdf'),
        'title': 'Thermodynamics Lecture Notes',
        'category_id': 'cat_3',
        'copyright_confirmed': 'true'
    })
    assert res1.status_code == 201
    user1_exp = db_service.get_profile_by_email("user_one@test.edu")['download_access_expires_at']

    # User 2 tries to upload the identical file
    token2 = get_auth_token(client, email="user_two@test.edu")
    headers2 = {'Authorization': f'Bearer {token2}'}

    res2 = client.post('/api/documents/upload', headers=headers2, data={
        'file': (io.BytesIO(pdf_bytes), 'Physics_Copy.pdf'),
        'title': 'Different Title But Same File',
        'category_id': 'cat_3',
        'copyright_confirmed': 'true'
    })
    assert res2.status_code == 409
    assert res2.get_json()['code'] == 'DUPLICATE_DOCUMENT'

    # User 2 should NOT have received access
    user2 = db_service.get_profile_by_email("user_two@test.edu")
    assert AccessService.is_access_active(user2) is False

    # User 1's expiry should NOT have been modified
    user1_after = db_service.get_profile_by_email("user_one@test.edu")
    assert user1_after['download_access_expires_at'] == user1_exp

# 7. Successful upload sends an upload confirmation email
def test_7_successful_upload_sends_upload_confirmation_email(test_setup):
    client = test_setup["client"]
    sent = test_setup["sent_emails"]

    token = get_auth_token(client, email="confirm_student@test.edu", name="Confirm Student")
    headers = {'Authorization': f'Bearer {token}'}

    pdf_bytes = create_valid_pdf_bytes("Data structures binary search trees notes.")
    res = client.post('/api/documents/upload', headers=headers, data={
        'file': (io.BytesIO(pdf_bytes), 'DSA_Trees.pdf'),
        'title': 'Binary Search Trees Guide',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    })
    assert res.status_code == 201

    # Check that an upload confirmation email was dispatched
    upload_emails = [e for e in sent if "Resource Uploaded Successfully" in e["subject"]]
    assert len(upload_emails) == 1
    assert upload_emails[0]["recipient_email"] == "confirm_student@test.edu"
    assert "24 Hours of Unlimited Downloads" in upload_emails[0]["text_content"]

# 8. An eligible user receives a reminder when 10 hours remain
def test_8_eligible_user_receives_reminder_when_10_hours_remain(test_setup):
    db_service = test_setup["db_service"]
    email_service = test_setup["email_service"]
    sent = test_setup["sent_emails"]

    # Create a user whose access expires in exactly 9 hours (within the 10-hour window)
    user = db_service.create_user("Reminder User", "reminder@test.edu", "hashed_pwd")
    now = datetime.datetime.now(datetime.timezone.utc)
    started = (now - datetime.timedelta(hours=15)).isoformat()
    expires = (now + datetime.timedelta(hours=9)).isoformat()
    db_service.update_user_access_expiry(user["id"], started, expires)

    reminder_svc = ReminderService(db_service=db_service, email_service=email_service)
    stats = reminder_svc.check_and_send_reminders()

    assert stats["eligible_found"] == 1
    assert stats["reminders_sent"] == 1

    reminder_emails = [e for e in sent if "10 Hours of Unlimited Access Remaining" in e["subject"] or "9 Hours" in e["subject"]]
    assert len(reminder_emails) == 1
    assert reminder_emails[0]["recipient_email"] == "reminder@test.edu"

    # Profile should record reminder_sent_for_expiry
    updated_user = db_service.get_profile_by_id(user["id"])
    assert updated_user["reminder_sent_for_expiry"] == expires
    assert updated_user["reminder_sent_at"] is not None

# 9. The same access period never receives duplicate reminders
def test_9_same_access_period_never_receives_duplicate_reminders(test_setup):
    db_service = test_setup["db_service"]
    email_service = test_setup["email_service"]
    sent = test_setup["sent_emails"]

    user = db_service.create_user("Idempotent User", "idempotent@test.edu", "hashed_pwd")
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = (now + datetime.timedelta(hours=8)).isoformat()
    db_service.update_user_access_expiry(user["id"], now.isoformat(), expires)

    reminder_svc = ReminderService(db_service=db_service, email_service=email_service)
    
    # First check: sends reminder
    stats1 = reminder_svc.check_and_send_reminders()
    assert stats1["reminders_sent"] == 1

    # Second check (e.g. 5 minutes later): should NOT send duplicate
    stats2 = reminder_svc.check_and_send_reminders()
    assert stats2["eligible_found"] == 0
    assert stats2["reminders_sent"] == 0

    # User still only received 1 reminder email
    user_reminders = [e for e in sent if e["recipient_email"] == "idempotent@test.edu"]
    assert len(user_reminders) == 1

# 10. Expired access does not receive a late reminder
def test_10_expired_access_does_not_receive_late_reminder(test_setup):
    db_service = test_setup["db_service"]
    email_service = test_setup["email_service"]
    sent = test_setup["sent_emails"]

    user = db_service.create_user("Expired User", "expired@test.edu", "hashed_pwd")
    now = datetime.datetime.now(datetime.timezone.utc)
    # Expired 2 hours ago
    started = (now - datetime.timedelta(hours=26)).isoformat()
    expires = (now - datetime.timedelta(hours=2)).isoformat()
    db_service.update_user_access_expiry(user["id"], started, expires)

    reminder_svc = ReminderService(db_service=db_service, email_service=email_service)
    stats = reminder_svc.check_and_send_reminders()

    assert stats["eligible_found"] == 0
    assert stats["reminders_sent"] == 0
    assert len([e for e in sent if e["recipient_email"] == "expired@test.edu"]) == 0

# 11. Restarting the application does not lose pending reminders
def test_11_restarting_application_does_not_lose_pending_reminders(test_setup):
    db_file = test_setup["db_file"]
    sent = test_setup["sent_emails"]

    # 1. User gets access in DB
    db1 = DBService(db_path=db_file)
    user = db1.create_user("Persist User", "persist@test.edu", "hashed_pwd")
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = (now + datetime.timedelta(hours=6)).isoformat()
    db1.update_user_access_expiry(user["id"], now.isoformat(), expires)

    # 2. Simulate complete application restart (new DBService, new ReminderService, new EmailService)
    db2 = DBService(db_path=db_file)
    email_svc2 = EmailService(api_key="test-key", sender_email="sender@test.edu", db_service=db2)
    email_svc2.set_mock_send_handler(lambda payload: sent.append(payload) or {"success": True, "status": "sent", "message_id": "restart-msg"})

    reminder_svc2 = ReminderService(db_service=db2, email_service=email_svc2)
    stats = reminder_svc2.check_and_send_reminders()

    assert stats["eligible_found"] == 1
    assert stats["reminders_sent"] == 1
    assert len([e for e in sent if e["recipient_email"] == "persist@test.edu"]) == 1

# 12. Brevo API failure does not break registration or valid uploads
def test_12_brevo_api_failure_does_not_break_registration_or_uploads(test_setup):
    client = test_setup["client"]
    email_service = test_setup["email_service"]

    # Force mock sender to simulate network failure / exception
    def failing_send(payload):
        raise RuntimeError("Brevo connection timeout or 503 error")

    email_service.set_mock_send_handler(failing_send)

    # Registration should still succeed and return 201
    reg_res = register_user(client, email="resilient@test.edu", name="Resilient Student")
    assert reg_res.status_code == 201
    token = reg_res.get_json()['token']

    # Upload should also still succeed, save document, and grant 24h access
    pdf_bytes = create_valid_pdf_bytes("Resilient test notes content.")
    up_res = client.post('/api/documents/upload', headers={'Authorization': f'Bearer {token}'}, data={
        'file': (io.BytesIO(pdf_bytes), 'Resilient_Notes.pdf'),
        'title': 'Resilient Notes',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    })
    assert up_res.status_code == 201
    assert up_res.get_json()['reward_granted'] is True

# 13. Missing environment variables produce safe and understandable errors
def test_13_missing_env_variables_produce_safe_understandable_errors():
    # Instantiate email service with missing/placeholder credentials
    unconfigured_svc = EmailService(
        api_key='replace_with_your_new_brevo_api_key',
        sender_email='your_verified_sender_email'
    )
    assert unconfigured_svc.is_configured() is False

    # Attempt send - should return structured failure without throwing uncaught exceptions or leaking
    result = unconfigured_svc.send_welcome_email({"id": "123", "email": "test@test.com", "full_name": "Test"})
    assert result["success"] is False
    assert result["status"] == "unconfigured"
    assert "not configured" in result["error"].lower()

# 14. Existing authentication and unrelated features continue working
def test_14_existing_features_continue_working(test_setup):
    client = test_setup["client"]

    # Health check
    h_res = client.get('/api/health')
    assert h_res.status_code == 200
    assert h_res.get_json()['status'] == 'ok'

    # Register & Login
    token = get_auth_token(client, email="features@test.edu")
    login_res = client.post('/api/auth/login', json={
        'email': 'features@test.edu',
        'password': 'Password123!'
    })
    assert login_res.status_code == 200
    assert 'token' in login_res.get_json()

    # /api/auth/me
    me_res = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_res.status_code == 200
    assert me_res.get_json()['user']['email'] == 'features@test.edu'

    # /api/documents list
    docs_res = client.get('/api/documents')
    assert docs_res.status_code == 200
    assert 'documents' in docs_res.get_json()
    assert 'categories' in docs_res.get_json()

# 15. Protected Admin Email Diagnostics & Test Dispatch
def test_15_protected_admin_email_diagnostics(test_setup):
    client = test_setup["client"]

    # Anonymous user should be rejected (401)
    anon_res = client.get('/api/admin/email-diagnostics')
    assert anon_res.status_code in (401, 403)

    # Admin login
    admin_login_res = client.post('/api/admin/login', json={
        'email': 'admin@studyvault.edu',
        'password': 'AdminPassword123!'
    })
    assert admin_login_res.status_code == 200
    admin_token = admin_login_res.get_json()['token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    # Admin access should succeed
    diag_res = client.get('/api/admin/email-diagnostics', headers=admin_headers)
    assert diag_res.status_code == 200
    diag_data = diag_res.get_json()
    assert 'is_configured' in diag_data
    assert 'recent_logs' in diag_data

    # Admin test email dispatch
    test_email_res = client.post('/api/admin/email-test', headers=admin_headers, json={
        'recipient': 'test_admin_recip@univ.edu'
    })
    assert test_email_res.status_code == 200
    assert test_email_res.get_json()['success'] is True

# 16. Diagnostic CLI Methods Resilience
def test_16_diagnostic_methods_resilience():
    unconfigured = EmailService(api_key="replace_with_your_new_brevo_api_key", sender_email="your_verified_sender_email")
    verification = unconfigured.verify_credentials()
    assert verification['valid'] is False
    assert 'placeholder' in verification['error']

    # check delivery status with invalid/mock ID
    status = unconfigured.check_delivery_status("mock-id")
    assert status['status'] == 'unknown'
