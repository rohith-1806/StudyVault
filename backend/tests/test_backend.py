import os
import io
import pytest
import datetime
from pypdf import PdfWriter
from app import create_app
from config import Config

class TestConfig(Config):
    TESTING = True
    AUTO_APPROVE = True
    SECRET_KEY = 'test-secret-key'
    ADMIN_EMAIL = 'admin@studyvault.edu'
    # Hash for 'AdminPassword123!'
    ADMIN_PASSWORD_HASH = 'scrypt:32768:8:1$xH2g8l9B4v2k0L5m$95096b79753065a78248bc3bebb0ef3878b273b4b0e50efb0ef7645bfbc094208a0d0d82dd2604ca75a5cb33a6f1947b19818b76db01b1df40003b573510e140'

def create_sample_pdf(text_content="Sample educational notes for study vault testing.", pages=1):
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=612, height=792)
        # Note: pypdf blank pages have 0 text unless added with canvas or annotations
    buf = io.BytesIO()
    # We can write a simple valid PDF binary with text stream
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj <</Length " + str(len(text_content) + 50).encode() + b">>\n"
        b"stream\nBT /F1 24 Tf 100 700 Td (" + text_content.encode() + b") Tj ET\nendstream\nendobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000236 00000 n\n0000000330 00000 n\n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n410\n%%EOF\n"
    )
    return pdf_bytes

def create_blank_pdf():
    return (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>> endobj\n"
        b"4 0 obj <</Length 0>>\nstream\n\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000195 00000 n\n"
        b"trailer <</Size 5 /Root 1 0 R>>\nstartxref\n245\n%%EOF\n"
    )

@pytest.fixture
def client(tmp_path):
    db_file = os.path.join(tmp_path, "test_database.db")
    app = create_app(TestConfig)
    app.config['DB_SERVICE'].db_path = db_file
    app.config['DB_SERVICE']._init_sqlite()
    with app.test_client() as client:
        yield client

def get_auth_headers(client, email="student@test.com", password="Password123!", name="Test Student"):
    res = client.post('/api/auth/register', json={
        'full_name': name,
        'email': email,
        'password': password,
        'confirm_password': password
    })
    token = res.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

def get_admin_headers(client):
    res = client.post('/api/admin/login', json={
        'email': 'admin@studyvault.edu',
        'password': 'AdminPassword123!'
    })
    token = res.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

# --- AUTH TEST CASES (19-24, 25-27) ---

def test_19_register_valid_account(client):
    res = client.post('/api/auth/register', json={
        'full_name': 'Alice Smith',
        'email': 'alice@university.edu',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    assert res.status_code == 201
    assert 'token' in res.get_json()

def test_20_register_duplicate_email(client):
    get_auth_headers(client, email="dupe@test.com")
    res = client.post('/api/auth/register', json={
        'full_name': 'Dupe User',
        'email': 'dupe@test.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    assert res.status_code == 400
    assert 'already exists' in res.get_json()['error']

def test_21_wrong_password_login(client):
    get_auth_headers(client, email="wrongpwd@test.com")
    res = client.post('/api/auth/login', json={
        'email': 'wrongpwd@test.com',
        'password': 'WrongPassword999!'
    })
    assert res.status_code == 401

def test_22_correct_login(client):
    get_auth_headers(client, email="loginuser@test.com", password="MySecretPassword123!")
    res = client.post('/api/auth/login', json={
        'email': 'loginuser@test.com',
        'password': 'MySecretPassword123!'
    })
    assert res.status_code == 200
    assert 'token' in res.get_json()

def test_23_student_tries_admin_api(client):
    headers = get_auth_headers(client, email="student_hacker@test.com")
    res = client.get('/api/admin/dashboard', headers=headers)
    assert res.status_code == 403

def test_24_unauthenticated_user_tries_protected_api(client):
    res = client.get('/api/profile')
    assert res.status_code == 401

def test_25_admin_login(client):
    headers = get_admin_headers(client)
    assert 'Authorization' in headers

def test_26_admin_wrong_password(client):
    res = client.post('/api/admin/login', json={
        'email': 'admin@studyvault.edu',
        'password': 'WrongAdminPassword'
    })
    assert res.status_code == 401

def test_27_student_attempts_admin_login(client):
    get_auth_headers(client, email="fakeadmin@test.com")
    res = client.post('/api/admin/login', json={
        'email': 'fakeadmin@test.com',
        'password': 'Password123!'
    })
    assert res.status_code == 401

# --- UPLOAD & DUPLICATE TEST CASES (1-10) ---

def test_01_upload_valid_pdf(client):
    headers = get_auth_headers(client, email="uploader1@test.com")
    pdf_data = create_sample_pdf("Valid Data Structures and Algorithms notes.")
    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'dsa_notes.pdf'),
        'title': 'Data Structures Notes',
        'category_id': 'cat_4',
        'course': 'CSE',
        'subject': 'DSA',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res.status_code == 201
    json_resp = res.get_json()
    assert json_resp['reward_granted'] is True
    assert json_resp['reward_info']['access_active'] is True

def test_02_upload_exact_duplicate_pdf(client):
    headers = get_auth_headers(client, email="uploader2@test.com")
    pdf_data = create_sample_pdf("Unique Operating Systems content.")
    
    # Upload first time
    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'os_notes.pdf'),
        'title': 'OS Notes',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201

    # Upload exact same file again
    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'os_notes_copy.pdf'),
        'title': 'OS Notes Duplicate',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res2.status_code in (400, 409)
    assert 'already' in str(res2.get_json()).lower() or 'duplicate' in str(res2.get_json()).lower()

def test_03_04_renamed_or_modified_metadata_duplicate(client):
    headers = get_auth_headers(client, email="uploader3@test.com")
    pdf_data = create_sample_pdf("Database Management Systems complete tutorial.")

    client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'dbms_original.pdf'),
        'title': 'DBMS Original',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    # Renamed filename with same content
    res_renamed = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'completely_new_filename.pdf'),
        'title': 'DBMS Renamed',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res_renamed.status_code in (400, 409)
    assert 'already' in str(res_renamed.get_json()).lower() or 'duplicate' in str(res_renamed.get_json()).lower()

def test_05_upload_blank_pdf(client):
    headers = get_auth_headers(client, email="blank_uploader@test.com")
    blank_data = create_blank_pdf()

    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(blank_data), 'empty.pdf'),
        'title': 'Empty Document',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res.status_code == 400
    assert 'blank' in res.get_json()['error'].lower()

def test_06_upload_corrupted_pdf(client):
    headers = get_auth_headers(client, email="corrupt_uploader@test.com")
    corrupt_bytes = b"%PDF-1.4\nSome random garbage corrupted string %EOF"

    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(corrupt_bytes), 'corrupt.pdf'),
        'title': 'Corrupt File',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res.status_code == 400

def test_07_upload_txt_renamed_to_pdf(client):
    headers = get_auth_headers(client, email="fake_pdf@test.com")
    fake_txt = b"Hello world! This is a plain text file renamed to pdf."

    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(fake_txt), 'fake.pdf'),
        'title': 'Fake PDF',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res.status_code == 400
    assert 'invalid magic header' in res.get_json()['error'].lower() or 'corrupted' in res.get_json()['error'].lower()

def test_10_unauthenticated_upload_rejected(client):
    pdf_data = create_sample_pdf("Unauthenticated attempt")
    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'test.pdf'),
        'copyright_confirmed': 'true'
    }, content_type='multipart/form-data')

    assert res.status_code == 401

# --- CONTRIBUTION REWARD & ACCESS TEST CASES (11-18) ---

def test_11_14_15_18_access_reward_and_authorization(client):
    # Student A uploads document
    headers_a = get_auth_headers(client, email="student_a@test.com")
    pdf_a = create_sample_pdf("Computer Networks notes by Student A.")
    
    upload_res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_a), 'cn_notes.pdf'),
        'title': 'CN Notes',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers_a, content_type='multipart/form-data')
    doc_id = upload_res.get_json()['document']['id']

    # Student A now has active 24h access -> Student A can download
    dl_res_a = client.get(f'/api/documents/{doc_id}/download', headers=headers_a)
    assert dl_res_a.status_code == 200

    # Student B has NO active access -> Student B blocked from downloading Student A's doc
    headers_b = get_auth_headers(client, email="student_b@test.com")
    dl_res_b = client.get(f'/api/documents/{doc_id}/download', headers=headers_b)
    assert dl_res_b.status_code == 403
    assert 'expired' in dl_res_b.get_json()['error'].lower() or 'upload a valid' in dl_res_b.get_json()['error'].lower()

    # Test 18: If Student A's access expires, Student A can STILL download their OWN document
    db_service = client.application.config['DB_SERVICE']
    user_a = db_service.get_profile_by_email('student_a@test.com')
    expired_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=10)).isoformat()
    db_service.update_user_access_expiry(user_a['id'], expired_time, expired_time)

    # Student A downloads own doc post-expiration
    dl_own_expired = client.get(f'/api/documents/{doc_id}/download', headers=headers_a)
    assert dl_own_expired.status_code == 200

# --- ADMIN TEST CASES (28-30) ---

def test_28_29_30_admin_moderation_and_user_status(client):
    admin_headers = get_admin_headers(client)

    # 1. List users
    users_res = client.get('/api/admin/users', headers=admin_headers)
    assert users_res.status_code == 200
    users_list = users_res.get_json()['users']
    assert len(users_list) > 0

    # 2. Toggle user status (Disable student user)
    target_user = users_list[0]
    toggle_res = client.patch(f'/api/admin/users/{target_user["id"]}/status', json={'is_active': False}, headers=admin_headers)
    assert toggle_res.status_code == 200
    assert toggle_res.get_json()['user']['is_active'] == 0

    # 3. Check Admin Dashboard Stats
    dash_res = client.get('/api/admin/dashboard', headers=admin_headers)
    assert dash_res.status_code == 200
    stats = dash_res.get_json()['stats']
    assert 'total_users' in stats
    assert 'total_documents' in stats

# --- VIEW TRACKING TEST CASES ---

def test_preview_view_increment_system(client):
    headers = get_auth_headers(client, email="viewer_test@test.com")
    pdf_data = create_sample_pdf("View tracking document test.")

    upload_res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'view_test.pdf'),
        'title': 'View Tracking Test Doc',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert upload_res.status_code == 201
    doc_id = upload_res.get_json()['document']['id']
    assert upload_res.get_json()['document']['views_count'] == 0

    # 1. Fetching document metadata or refreshing library must NOT increment views
    get_res = client.get(f'/api/documents/{doc_id}', headers=headers)
    assert get_res.status_code == 200
    assert get_res.get_json()['document']['views_count'] == 0

    # 2. Recording preview load increments count by 1
    view_res_1 = client.post(f'/api/documents/{doc_id}/view', headers=headers)
    assert view_res_1.status_code == 200
    assert view_res_1.get_json()['views_count'] == 1
    assert view_res_1.get_json()['document_id'] == doc_id

    # 3. Verify count in database persists and is reflected in GET
    doc_after_1 = client.get(f'/api/documents/{doc_id}', headers=headers).get_json()['document']
    assert doc_after_1['views_count'] == 1

    # 4. A second successful preview opening event increments count to 2
    view_res_2 = client.post(f'/api/documents/{doc_id}/view', headers=headers)
    assert view_res_2.status_code == 200
    assert view_res_2.get_json()['views_count'] == 2

    # 5. Non-existent document returns 404
    view_404 = client.post('/api/documents/non_existent_uuid_12345/view')
    assert view_404.status_code == 404

def test_client_cannot_arbitrarily_manipulate_views(client):
    headers = get_auth_headers(client, email="security_tester@test.com")
    pdf_data = create_sample_pdf("Security test for view manipulation.")

    upload_res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'security_test.pdf'),
        'title': 'Security Test Doc',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    doc_id = upload_res.get_json()['document']['id']

    # Attempt to supply arbitrary client views_count in payload
    hack_res = client.post(f'/api/documents/{doc_id}/view', json={
        'views_count': 999999,
        'arbitrary_count': 500
    })
    assert hack_res.status_code == 200
    # Must only increment by 1 safely, ignoring client payload
    assert hack_res.get_json()['views_count'] == 1

    # In database, views_count is exactly 1
    doc_db = client.application.config['DB_SERVICE'].get_document_by_id(doc_id)
    assert doc_db['views_count'] == 1


# =====================================================================
# 14 STRICT DUPLICATE PDF DETECTION AUTOMATED TEST CASES (REQUIRED)
# =====================================================================

def test_case_01_identical_title(client):
    """Test Case 1 — Identical Title: Data Visualization Unit 1.pdf vs Data Visualization Unit 1.pdf"""
    headers = get_auth_headers(client, email="tc1_user@test.com")
    pdf_bytes = create_sample_pdf("Content for Data Visualization Unit 1.")

    # Upload existing document
    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'Data Visualization Unit 1.pdf'),
        'title': 'Data Visualization Unit 1.pdf',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201
    orig_id = res1.get_json()['document']['id']

    # Upload duplicate with identical title (with different bytes to test pure title matching)
    different_bytes = create_sample_pdf("Different content for DV Unit 1 notes.")
    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(different_bytes), 'Data Visualization Unit 1.pdf'),
        'title': 'Data Visualization Unit 1.pdf',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res2.status_code == 409
    body = res2.get_json()
    assert body['code'] == 'DUPLICATE_DOCUMENT'
    assert body['duplicate_type'] == 'title'
    assert body['existing_document']['id'] == orig_id


def test_case_02_case_insensitive_title(client):
    """Test Case 2 — Case-Insensitive Title: DBMS Notes.pdf vs dbms notes.PDF"""
    headers = get_auth_headers(client, email="tc2_user@test.com")
    pdf_bytes1 = create_sample_pdf("Content for DBMS Notes.")
    pdf_bytes2 = create_sample_pdf("Distinct content for case insensitive test.")

    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes1), 'DBMS Notes.pdf'),
        'title': 'DBMS Notes.pdf',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201

    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes2), 'dbms notes.PDF'),
        'title': 'dbms notes.PDF',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res2.status_code == 409
    assert res2.get_json()['code'] == 'DUPLICATE_DOCUMENT'
    assert res2.get_json()['duplicate_type'] == 'title'


def test_case_03_whitespace_and_extension_normalization(client):
    """Test Case 3 — Whitespace and Extension Normalization: '  Python Notes.pdf' vs 'Python   Notes'"""
    headers = get_auth_headers(client, email="tc3_user@test.com")
    pdf_bytes1 = create_sample_pdf("Python notes content 1.")
    pdf_bytes2 = create_sample_pdf("Python notes content 2.")

    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes1), 'python_notes.pdf'),
        'title': '  Python Notes.pdf',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201

    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes2), 'python_notes_2.pdf'),
        'title': 'Python   Notes',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res2.status_code == 409
    assert res2.get_json()['code'] == 'DUPLICATE_DOCUMENT'
    assert res2.get_json()['duplicate_type'] == 'title'


def test_case_04_same_content_different_filename(client):
    """Test Case 4 — Same Content, Different Filename: Unit1.pdf vs ChapterOne.pdf"""
    headers = get_auth_headers(client, email="tc4_user@test.com")
    exact_same_bytes = create_sample_pdf("Exact identical binary PDF bytes content across both files.")

    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(exact_same_bytes), 'Unit1.pdf'),
        'title': 'Unit 1 Unique Title',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201
    first_doc_id = res1.get_json()['document']['id']

    # Upload exact same bytes with completely different filename & title
    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(exact_same_bytes), 'ChapterOne.pdf'),
        'title': 'Chapter One Distinct Title',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res2.status_code == 409
    assert res2.get_json()['code'] == 'DUPLICATE_DOCUMENT'
    assert res2.get_json()['duplicate_type'] == 'content_hash'
    assert res2.get_json()['existing_document']['id'] == first_doc_id


def test_case_05_same_filename_different_content(client):
    """Test Case 5 — Same Filename, Different Content: DBMS Notes.pdf vs DBMS Notes.pdf with different content"""
    headers = get_auth_headers(client, email="tc5_user@test.com")
    pdf_bytes1 = create_sample_pdf("DBMS Notes version A.")
    pdf_bytes2 = create_sample_pdf("DBMS Notes version B genuinely different.")

    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes1), 'DBMS Notes.pdf'),
        'title': 'DBMS Notes.pdf',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201
    orig_id = res1.get_json()['document']['id']

    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes2), 'DBMS Notes.pdf'),
        'title': 'DBMS Notes.pdf',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res2.status_code == 409
    assert res2.get_json()['code'] == 'DUPLICATE_DOCUMENT'
    assert res2.get_json()['duplicate_type'] == 'title'

    # Ensure original document was never overwritten
    db_service = client.application.config['DB_SERVICE']
    orig_doc = db_service.get_document_by_id(orig_id)
    assert orig_doc is not None
    assert orig_doc['title'] == 'DBMS Notes.pdf'


def test_case_06_different_units(client):
    """Test Case 6 — Different Units: DBMS Unit 1.pdf vs DBMS Unit 2.pdf"""
    headers = get_auth_headers(client, email="tc6_user@test.com")
    pdf_unit1 = create_sample_pdf("DBMS Unit 1 Relational Models and ER Diagrams.")
    pdf_unit2 = create_sample_pdf("DBMS Unit 2 SQL Queries Normalization and Indexing.")

    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_unit1), 'DBMS Unit 1.pdf'),
        'title': 'DBMS Unit 1.pdf',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201

    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_unit2), 'DBMS Unit 2.pdf'),
        'title': 'DBMS Unit 2.pdf',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    # Both documents must be accepted without false duplicate rejection
    assert res2.status_code == 201
    assert res1.get_json()['document']['id'] != res2.get_json()['document']['id']


def test_case_07_same_title_different_capitalization(client):
    """Test Case 7 — Same Title, Different Capitalization: Quantum Physics.pdf vs QUANTUM PHYSICS.pdf"""
    headers = get_auth_headers(client, email="tc7_user@test.com")
    pdf_bytes1 = create_sample_pdf("Quantum physics notes lower.")
    pdf_bytes2 = create_sample_pdf("Quantum physics notes upper.")

    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes1), 'Quantum Physics.pdf'),
        'title': 'Quantum Physics.pdf',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201

    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes2), 'QUANTUM PHYSICS.pdf'),
        'title': 'QUANTUM PHYSICS.pdf',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res2.status_code == 409
    assert res2.get_json()['code'] == 'DUPLICATE_DOCUMENT'
    assert res2.get_json()['duplicate_type'] == 'title'


def test_case_08_completely_new_pdf(client):
    """Test Case 8 — Completely New PDF: Valid PDF with unique title and content"""
    headers = get_auth_headers(client, email="tc8_user@test.com")
    pdf_data = create_sample_pdf("Unique Artificial Intelligence Neural Networks guide.")

    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_data), 'ai_neural_networks.pdf'),
        'title': 'Deep Neural Networks Guide 2026',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res.status_code == 201
    doc = res.get_json()['document']
    assert doc['title'] == 'Deep Neural Networks Guide 2026'
    assert doc['file_hash'] != ''
    assert doc['status'] == 'approved'


def test_case_09_empty_or_invalid_pdf(client):
    """Test Case 9 — Empty or Invalid PDF: zero-byte, blank or corrupted file"""
    headers = get_auth_headers(client, email="tc9_user@test.com")

    # 1. Zero-byte file
    res_empty = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(b""), 'empty.pdf'),
        'title': 'Empty Document',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res_empty.status_code == 400

    # 2. Blank PDF with 0 pages
    blank_data = create_blank_pdf()
    res_blank = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(blank_data), 'blank.pdf'),
        'title': 'Blank Document',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res_blank.status_code == 400

    # 3. Non-PDF text file renamed with .pdf extension
    res_txt = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(b"Plain text file not a real pdf."), 'fake.pdf'),
        'title': 'Fake Document',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res_txt.status_code == 400


def test_case_10_concurrent_identical_uploads(client):
    """Test Case 10 — Concurrent Identical Uploads: Two simultaneous requests uploading same content"""
    import concurrent.futures
    app = client.application
    headers = get_auth_headers(client, email="tc10_user@test.com")
    pdf_bytes = create_sample_pdf("Concurrent identical upload test binary data.")

    def upload_concurrent(idx):
        with app.test_client() as c:
            return c.post('/api/documents/upload', data={
                'file': (io.BytesIO(pdf_bytes), f'concurrent_{idx}.pdf'),
                'title': f'Concurrent Test Document {idx}',
                'category_id': 'cat_1',
                'copyright_confirmed': 'true'
            }, headers=headers, content_type='multipart/form-data')

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(upload_concurrent, 1)
        f2 = executor.submit(upload_concurrent, 2)
        r1 = f1.result()
        r2 = f2.result()

    statuses = [r1.status_code, r2.status_code]
    assert 201 in statuses, f"At least one upload must succeed (got {statuses})"
    assert 409 in statuses, f"The duplicate upload must be rejected with 409 (got {statuses})"


def test_case_11_existing_legacy_documents(client):
    """Test Case 11 — Existing Legacy Documents: Legacy record without stored checksum is checked safely"""
    headers = get_auth_headers(client, email="tc11_user@test.com")
    pdf_bytes = create_sample_pdf("Content for legacy document without stored checksum.")

    # 1. Create a document normally
    res1 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'legacy_original.pdf'),
        'title': 'Legacy Original Document',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res1.status_code == 201
    doc_id = res1.get_json()['document']['id']

    # 2. Simulate legacy unhashed document by blanking file_hash in database
    db_service = client.application.config['DB_SERVICE']
    conn = db_service._get_sqlite_conn()
    conn.execute('UPDATE documents SET file_hash = "" WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()

    # 3. Upload same PDF bytes with a different title
    res2 = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'new_name.pdf'),
        'title': 'Completely Different Title From Legacy',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    # Must check stored contents of legacy doc and reject as duplicate!
    assert res2.status_code == 409
    assert res2.get_json()['code'] == 'DUPLICATE_DOCUMENT'
    assert res2.get_json()['duplicate_type'] == 'content_hash'


def test_case_12_storage_failure(client, monkeypatch):
    """Test Case 12 — Storage Failure: Storage upload failure produces clean error without orphaned DB record"""
    headers = get_auth_headers(client, email="tc12_user@test.com")
    pdf_bytes = create_sample_pdf("Storage failure simulation text.")
    storage_service = client.application.config['STORAGE_SERVICE']

    def mock_storage_fail(*args, **kwargs):
        raise IOError("Supabase Storage timeout error simulated")

    monkeypatch.setattr(storage_service, 'upload_document_pdf', mock_storage_fail)

    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'fail_test.pdf'),
        'title': 'Storage Failure Simulation Doc',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')

    assert res.status_code == 500
    assert res.get_json()['code'] == 'STORAGE_ERROR'

    # Verify no document record was created
    db_service = client.application.config['DB_SERVICE']
    assert db_service.find_document_by_title_normalized('storage failure simulation doc') is None


def test_case_13_unauthorized_upload(client):
    """Test Case 13 — Unauthorized Upload: Unauthenticated request rejected with 401 without DB or storage object"""
    pdf_bytes = create_sample_pdf("Unauthorized user attempt bytes.")

    res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'unauth.pdf'),
        'title': 'Unauthorized Attempt Doc',
        'category_id': 'cat_1',
        'copyright_confirmed': 'true'
    }, content_type='multipart/form-data')

    assert res.status_code == 401
    db_service = client.application.config['DB_SERVICE']
    assert db_service.find_document_by_title_normalized('unauthorized attempt doc') is None


def test_case_14_duplicate_check_does_not_break_normal_uploads(client):
    """Test Case 14 — Duplicate Check Does Not Break Normal Uploads: Two different valid PDFs both accepted"""
    headers = get_auth_headers(client, email="tc14_user@test.com")
    pdf_a = create_sample_pdf("Completely unique content for Document Alpha Machine Learning.")
    pdf_b = create_sample_pdf("Completely unique content for Document Beta Cloud Computing Architecture.")

    res_a = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_a), 'doc_alpha.pdf'),
        'title': 'Document Alpha Machine Learning',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res_a.status_code == 201

    res_b = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_b), 'doc_beta.pdf'),
        'title': 'Document Beta Cloud Computing Architecture',
        'category_id': 'cat_4',
        'copyright_confirmed': 'true'
    }, headers=headers, content_type='multipart/form-data')
    assert res_b.status_code == 201

    assert res_a.get_json()['document']['id'] != res_b.get_json()['document']['id']


