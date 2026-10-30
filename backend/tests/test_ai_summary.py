import os
import io
import pytest
import datetime
from app import create_app
from config import Config
from services.ai_service import (
    AIService,
    ScannedPDFError,
    EmptyPDFError,
    CorruptedPDFError,
    AIRateLimitError,
    AIProviderConfigError
)

class TestConfig(Config):
    TESTING = True
    AUTO_APPROVE = True
    SECRET_KEY = 'test-secret-key'
    ADMIN_EMAIL = 'admin@studyvault.edu'
    ADMIN_PASSWORD_HASH = 'scrypt:32768:8:1$xH2g8l9B4v2k0L5m$95096b79753065a78248bc3bebb0ef3878b273b4b0e50efb0ef7645bfbc094208a0d0d82dd2604ca75a5cb33a6f1947b19818b76db01b1df40003b573510e140'
    AI_MOCK = True

def make_valid_pdf_with_text(text: str) -> bytes:
    """Generates a valid single-page PDF with precise xref byte offsets."""
    safe_text = text.replace("(", "\\(").replace(")", "\\)")
    stream_content = f"BT /F1 24 Tf 50 700 Td ({safe_text}) Tj ET\n".encode("latin-1")
    obj1 = b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    obj2 = b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    obj3 = b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    obj4 = f"4 0 obj <</Length {len(stream_content)}>>\nstream\n".encode("latin-1") + stream_content + b"endstream\nendobj\n"
    obj5 = b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
    
    header = b"%PDF-1.4\n"
    offsets = [0]
    offsets.append(len(header))
    offsets.append(offsets[-1] + len(obj1))
    offsets.append(offsets[-1] + len(obj2))
    offsets.append(offsets[-1] + len(obj3))
    offsets.append(offsets[-1] + len(obj4))
    
    body = header + obj1 + obj2 + obj3 + obj4 + obj5
    xref_offset = len(body)
    
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("ascii")
    
    trailer = f"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    return body + xref + trailer

def create_scanned_pdf_bytes():
    """Generates a valid PDF with minimal alphanumeric text (< 50 chars) simulating scanned pages."""
    return make_valid_pdf_with_text("Scan")

@pytest.fixture
def client_app(tmp_path):
    db_file = os.path.join(tmp_path, "test_summary.db")
    storage_dir = os.path.join(tmp_path, "storage_data")
    os.makedirs(storage_dir, exist_ok=True)

    app = create_app(TestConfig)
    app.config['DB_SERVICE'].db_path = db_file
    app.config['DB_SERVICE']._init_sqlite()
    app.config['LOCAL_STORAGE_DIR'] = storage_dir

    with app.test_client() as client:
        yield client, app

def get_auth_headers(client, email="student@studyvault.edu", name="Test Student"):
    res = client.post('/api/auth/register', json={
        'full_name': name,
        'email': email,
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    token = res.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

# ===========================================================================
# 1. AIService Unit Tests
# ===========================================================================

def test_ai_service_extract_text_valid():
    service = AIService(mock=True)
    sample_text = "Operating Systems Unit 1 Notes: Process Scheduling, Threads, and Deadlocks in modern kernels."
    pdf_bytes = make_valid_pdf_with_text(sample_text)
    
    text, pages, chars = service.extract_text_from_pdf_bytes(pdf_bytes)
    assert pages == 1
    assert chars >= 50
    assert "Operating Systems" in text

def test_ai_service_scanned_pdf_rejection():
    service = AIService(mock=True)
    scanned_bytes = create_scanned_pdf_bytes()
    
    with pytest.raises(ScannedPDFError) as exc_info:
        service.extract_text_from_pdf_bytes(scanned_bytes)
    assert exc_info.value.code == "SCANNED_PDF_NO_TEXT"

def test_ai_service_empty_and_corrupt_pdf():
    service = AIService(mock=True)
    with pytest.raises(EmptyPDFError):
        service.extract_text_from_pdf_bytes(b"")

    with pytest.raises(CorruptedPDFError):
        service.extract_text_from_pdf_bytes(b"%PDF-1.4 this is a corrupted file payload")

def test_ai_service_chunking():
    service = AIService(mock=True)
    short_text = "A" * 500
    assert len(service.chunk_text(short_text, chunk_size=1000)) == 1

    # Text larger than chunk size
    long_text = "\n\n".join([f"Paragraph {i}: " + ("content " * 100) for i in range(25)])
    chunks = service.chunk_text(long_text, chunk_size=2000, overlap=200)
    assert len(chunks) > 1

def test_ai_service_parse_summary_markdown():
    service = AIService(mock=True)
    mock_md = """## Overview
This is a comprehensive overview of Distributed Systems concepts.

## Key Points
- Paxos consensus algorithm guarantees safety under asynchronous networks.
- Raft decomposes consensus into leader election, log replication, and safety.
- CAP theorem states consistency, availability, and partition tolerance tradeoffs.

## Important Definitions
- **Quorum**: The minimum number of cluster members that must agree on a transaction.
- **Split Brain**: A condition where a cluster divides into two independent sub-clusters.

## Exam Revision Notes
- High probability exam question: Compare Paxos vs Raft leader election mechanism.
- Common pitfall: Do not assume linearizability implies causal consistency.

## Conclusion
Distributed consensus ensures fault-tolerant state machine replication in modern cloud architecture."""

    parsed = service.parse_summary_markdown(mock_md)
    assert "Distributed Systems" in parsed["overview"]
    assert len(parsed["key_points"]) == 3
    assert len(parsed["important_definitions"]) == 2
    assert parsed["important_definitions"][0]["term"] == "Quorum"
    assert len(parsed["exam_revision_notes"]) == 2
    assert "Distributed consensus" in parsed["conclusion"]

def test_ai_service_summarize_pdf_returns_all_five_sections():
    service = AIService(mock=True)
    sample_text = "Computer Networks and Protocol Layers: Physical, Data Link, Network, Transport, and Application layers."
    pdf_bytes = make_valid_pdf_with_text(sample_text)

    result = service.summarize_pdf(pdf_bytes, doc_title="Computer Networks")
    assert result["title"] == "Computer Networks"
    assert result["page_count"] == 1
    summary = result["summary"]
    assert summary["overview"]
    assert len(summary["key_points"]) > 0
    assert len(summary["important_definitions"]) > 0
    assert len(summary["exam_revision_notes"]) > 0
    assert summary["conclusion"]

# ===========================================================================
# 2. Flask Endpoint /api/documents/<doc_id>/summarize Integration Tests
# ===========================================================================

def test_summarize_requires_authentication(client_app):
    client, _ = client_app
    res = client.post('/api/documents/doc-123/summarize')
    assert res.status_code == 401

def test_summarize_non_existent_document_returns_404(client_app):
    client, _ = client_app
    headers = get_auth_headers(client, email="alice@test.com")
    res = client.post('/api/documents/non-existent-id/summarize', headers=headers)
    assert res.status_code == 404

def test_summarize_authorized_uploader_succeeds_and_caches(client_app):
    client, app = client_app
    headers = get_auth_headers(client, email="uploader@test.com")

    # 1. Upload a valid document
    pdf_text = "Software Engineering Principles: Agile, Scrum, CI/CD, Microservices, and Refactoring Patterns."
    pdf_bytes = make_valid_pdf_with_text(pdf_text)
    
    upload_res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'software_eng.pdf'),
        'title': 'Software Engineering Notes',
        'copyright_confirmed': 'true',
        'category_id': 'cat_4'
    }, headers=headers, content_type='multipart/form-data')
    
    assert upload_res.status_code == 201
    doc_id = upload_res.get_json()['document']['id']

    # 2. Call GET /api/documents/<doc_id>/summary before summarization (not cached yet)
    check_res = client.get(f'/api/documents/{doc_id}/summary', headers=headers)
    assert check_res.status_code == 200
    assert check_res.get_json()['cached'] is False

    # 3. Call POST /api/documents/<doc_id>/summarize for the first time
    sum_res = client.post(f'/api/documents/{doc_id}/summarize', headers=headers)
    assert sum_res.status_code == 200
    data = sum_res.get_json()
    assert data['success'] is True
    assert data['cached'] is False
    assert data['document_id'] == doc_id
    summary = data['summary']
    assert summary['overview']
    assert len(summary['key_points']) >= 1
    assert len(summary['important_definitions']) >= 1
    assert len(summary['exam_revision_notes']) >= 1
    assert summary['conclusion']

    # 4. Call POST /api/documents/<doc_id>/summarize a second time -> MUST be cached!
    cached_res = client.post(f'/api/documents/{doc_id}/summarize', headers=headers)
    assert cached_res.status_code == 200
    cached_data = cached_res.get_json()
    assert cached_data['cached'] is True
    assert cached_data['summary']['overview'] == summary['overview']

    # 5. GET /api/documents/<doc_id>/summary now reflects cached summary
    check_after = client.get(f'/api/documents/{doc_id}/summary', headers=headers)
    assert check_after.status_code == 200
    assert check_after.get_json()['cached'] is True

def test_summarize_permission_denied_when_access_expired(client_app):
    client, app = client_app
    uploader_headers = get_auth_headers(client, email="author@test.com")

    # Author uploads a document
    pdf_text = "Database Management Systems: SQL, Indexing, B-Trees, Normalization, ACID Properties."
    pdf_bytes = make_valid_pdf_with_text(pdf_text)
    up_res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'dbms.pdf'),
        'title': 'DBMS Comprehensive Notes',
        'copyright_confirmed': 'true',
        'category_id': 'cat_4'
    }, headers=uploader_headers, content_type='multipart/form-data')
    doc_id = up_res.get_json()['document']['id']

    # Another user registers (has no upload contribution -> access expired/inactive)
    viewer_headers = get_auth_headers(client, email="viewer@test.com")

    # Viewer tries to summarize without active download access
    res = client.post(f'/api/documents/{doc_id}/summarize', headers=viewer_headers)
    assert res.status_code == 403
    assert res.get_json()['code'] == 'ACCESS_DENIED'

def test_summarize_admin_always_authorized(client_app):
    client, app = client_app
    uploader_headers = get_auth_headers(client, email="student_doc@test.com")

    pdf_text = "Compiler Design: Lexical Analysis, Context-Free Grammars, LL(1) and LR Parsers."
    pdf_bytes = make_valid_pdf_with_text(pdf_text)
    up_res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(pdf_bytes), 'compilers.pdf'),
        'title': 'Compiler Design Lecture Notes',
        'copyright_confirmed': 'true',
        'category_id': 'cat_4'
    }, headers=uploader_headers, content_type='multipart/form-data')
    doc_id = up_res.get_json()['document']['id']

    # Login as admin
    admin_res = client.post('/api/admin/login', json={
        'email': 'admin@studyvault.edu',
        'password': 'AdminPassword123!'
    })
    admin_token = admin_res.get_json()['token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    # Admin summarizes document -> should succeed
    res = client.post(f'/api/documents/{doc_id}/summarize', headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()['success'] is True

def test_scanned_pdf_summarize_returns_clear_error(client_app):
    client, app = client_app
    headers = get_auth_headers(client, email="scanned_uploader@test.com")

    # Upload scanned PDF with < 50 characters (passes blank check because total_text_length >= 4 or page object)
    # create valid pdf with 10 chars
    scanned_bytes = make_valid_pdf_with_text("Minimal Text")
    up_res = client.post('/api/documents/upload', data={
        'file': (io.BytesIO(scanned_bytes), 'handwritten_scanned.pdf'),
        'title': 'Scanned Notes Document',
        'copyright_confirmed': 'true',
        'category_id': 'cat_15'
    }, headers=headers, content_type='multipart/form-data')

    assert up_res.status_code == 201
    doc_id = up_res.get_json()['document']['id']

    # Attempt to summarize scanned PDF
    res = client.post(f'/api/documents/{doc_id}/summarize', headers=headers)
    assert res.status_code == 400
    data = res.get_json()
    assert data['code'] == 'SCANNED_PDF_NO_TEXT'
    assert "scanned image" in data['error'].lower()
