import io
import uuid
import threading
import sqlite3
from flask import Blueprint, request, jsonify, current_app, send_file, redirect
from utils.security import login_required, get_current_user_from_request
from services.pdf_validator import validate_pdf_file, PDFValidationError
from services.duplicate_detector import compute_file_hash, compute_content_hash, check_is_duplicate, normalize_title
from services.access_service import AccessService
from services.ai_service import AIServiceError

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
_upload_lock = threading.RLock()

@documents_bp.route('', methods=['GET'])
def list_documents():
    category_id = request.args.get('category_id') or request.args.get('category')
    search = request.args.get('search')
    course = request.args.get('course')
    sort_by = request.args.get('sort_by', 'latest')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit

    db_service = current_app.config['DB_SERVICE']
    docs = db_service.list_documents(
        category_id=category_id,
        search=search,
        course=course,
        status='approved',
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )

    categories = db_service.list_categories()
    
    return jsonify({
        'documents': docs,
        'categories': categories,
        'page': page,
        'limit': limit
    }), 200

@documents_bp.route('/<doc_id>', methods=['GET'])
def get_document(doc_id):
    db_service = current_app.config['DB_SERVICE']
    doc = db_service.get_document_by_id(doc_id)
    
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    # Check if current user can download
    current_user = get_current_user_from_request()
    can_download = False
    access_expired_message = None

    if current_user:
        authorized, msg = AccessService.authorize_download(db_service, current_user['id'], doc)
        can_download = authorized
        if not authorized and doc['status'] == 'approved':
            access_expired_message = msg

    return jsonify({
        'document': doc,
        'can_download': can_download,
        'download_message': access_expired_message
    }), 200

@documents_bp.route('/<doc_id>/view', methods=['POST'])
def record_document_view(doc_id):
    db_service = current_app.config['DB_SERVICE']
    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    current_user = get_current_user_from_request()
    user_id = current_user.get('id') if current_user else None

    # Safe atomic database increment
    updated_views = db_service.increment_views(doc_id, user_id=user_id)
    return jsonify({
        'document_id': doc_id,
        'views_count': updated_views
    }), 200

@documents_bp.route('/upload', methods=['POST'])
@login_required
def upload_document(current_user):
    user_id = current_user['id']
    db_service = current_app.config['DB_SERVICE']
    storage_service = current_app.config['STORAGE_SERVICE']

    user_profile = db_service.get_profile_by_id(user_id)
    if not user_profile or not user_profile.get('is_active', 1):
        return jsonify({'error': 'Your account is disabled.'}), 403

    # Check copyright confirmation
    copyright_confirmed = request.form.get('copyright_confirmed', '').lower() in ('true', '1', 'yes')
    if not copyright_confirmed:
        return jsonify({'error': 'You must confirm that you created this document or have permission to share it.'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400

    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'Please select a valid PDF file.'}), 400

    file_bytes = file.read()
    filename = file.filename

    # 1. Server-side PDF validation
    try:
        val_result = validate_pdf_file(file_bytes, filename)
    except PDFValidationError as e:
        return jsonify({'error': e.message, 'code': e.code}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to process PDF: {str(e)}', 'code': 'VALIDATION_FAILED'}), 400

    # Extract & normalize title
    raw_title = request.form.get('title', '').strip()
    if not raw_title:
        raw_title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
    title = raw_title
    norm_title = normalize_title(title)

    category_id = request.form.get('category_id', 'cat_15')
    description = request.form.get('description', '').strip()
    course = request.form.get('course', '').strip()
    subject = request.form.get('subject', '').strip()
    semester = request.form.get('semester', '').strip()
    tags = request.form.get('tags', '').strip()

    # Calculate SHA-256 and content fingerprints
    file_hash = compute_file_hash(file_bytes)
    content_hash = compute_content_hash(
        extracted_text=val_result['extracted_text'],
        page_count=val_result['page_count'],
        file_size=val_result['file_size']
    )

    # 2. Concurrency-Safe Duplicate Detection (Title matching, SHA-256 Checksum, Content Hash)
    with _upload_lock:
        is_dup, existing_doc, dup_type = check_is_duplicate(
            db_service=db_service,
            file_hash=file_hash,
            content_hash=content_hash,
            title=title,
            storage_service=storage_service
        )
        if is_dup:
            existing_id = existing_doc.get('id') if existing_doc else None
            existing_title = existing_doc.get('title') if existing_doc else title
            msg = (
                f"A document with the title '{existing_title}' already exists in StudyVault." 
                if dup_type == 'title' 
                else "This document already exists in StudyVault."
            )
            return jsonify({
                'success': False,
                'code': 'DUPLICATE_DOCUMENT',
                'message': msg,
                'error': msg,
                'duplicate_type': dup_type,
                'existing_document': {
                    'id': existing_id,
                    'title': existing_title
                },
                'existing_document_id': existing_id
            }), 409

        # 3. Upload to Storage ONLY AFTER duplicate check passes completely
        doc_id = str(uuid.uuid4())
        try:
            storage_path = storage_service.upload_document_pdf(
                user_id=user_id,
                document_id=doc_id,
                file_bytes=file_bytes,
                filename=filename
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'code': 'STORAGE_ERROR',
                'error': f'Failed to store file: {str(e)}'
            }), 500

        auto_approve = current_app.config.get('AUTO_APPROVE', True)
        status = 'approved' if auto_approve else 'pending_review'

        doc_data = {
            'id': doc_id,
            'uploader_id': user_id,
            'uploader_name': user_profile.get('full_name', 'Student'),
            'title': title,
            'normalized_title': norm_title,
            'description': description,
            'category_id': category_id,
            'course': course,
            'subject': subject,
            'semester': semester,
            'tags': tags,
            'storage_path': storage_path,
            'file_name': filename,
            'file_size': val_result['file_size'],
            'page_count': val_result['page_count'],
            'mime_type': 'application/pdf',
            'file_hash': file_hash,
            'content_hash': content_hash,
            'status': status
        }

        # 4. Insert into database with immediate orphan cleanup on error
        try:
            created_doc = db_service.create_document(doc_data)
        except Exception as e:
            # Clean up orphaned storage object
            try:
                storage_service.delete_document_pdf(storage_path)
            except Exception as cleanup_err:
                print(f"[Storage Cleanup Error]: {cleanup_err}")

            if isinstance(e, sqlite3.IntegrityError) or 'unique' in str(e).lower():
                existing_dup = (
                    db_service.find_document_by_file_hash(file_hash) or 
                    db_service.find_document_by_title_normalized(norm_title)
                )
                existing_id = existing_dup.get('id') if existing_dup else None
                existing_title = existing_dup.get('title') if existing_dup else title
                return jsonify({
                    'success': False,
                    'code': 'DUPLICATE_DOCUMENT',
                    'message': 'This document already exists in StudyVault.',
                    'error': 'This document already exists in StudyVault.',
                    'duplicate_type': 'content_hash' if (existing_dup and existing_dup.get('file_hash') == file_hash) else 'title',
                    'existing_document': {
                        'id': existing_id,
                        'title': existing_title
                    },
                    'existing_document_id': existing_id
                }), 409

            return jsonify({
                'success': False,
                'code': 'DATABASE_ERROR',
                'error': f'Failed to save document metadata: {str(e)}'
            }), 500

        reward_info = None
        if status == 'approved':
            reward_duration = current_app.config.get('REWARD_DURATION_HOURS', 24)
            reward_info = AccessService.grant_24h_access(
                db_service=db_service,
                user_id=user_id,
                document_id=doc_id,
                duration_hours=reward_duration
            )

            # Dispatch Upload Confirmation & 24h Access Unlock Email via Brevo
            email_service = current_app.config.get('EMAIL_SERVICE')
            if email_service:
                if current_app.config.get('TESTING'):
                    try:
                        email_service.send_upload_confirmation_email(user_profile, created_doc, reward_info)
                    except Exception as e:
                        current_app.logger.warning(f"Upload confirmation test dispatch notice: {e}")
                else:
                    email_service.dispatch_async(
                        email_service.send_upload_confirmation_email,
                        user_profile,
                        created_doc,
                        reward_info
                    )

        return jsonify({
            'success': True,
            'message': 'Contribution added successfully!' if status == 'approved' else 'Document uploaded and pending moderation.',
            'document': created_doc,
            'reward_granted': status == 'approved',
            'reward_info': reward_info
        }), 201

@documents_bp.route('/<doc_id>/download', methods=['GET'])
@login_required
def download_document(current_user, doc_id):
    user_id = current_user['id']
    db_service = current_app.config['DB_SERVICE']
    storage_service = current_app.config['STORAGE_SERVICE']

    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    # 1. Authorization check
    authorized, message = AccessService.authorize_download(db_service, user_id, doc)
    if not authorized:
        return jsonify({
            'error': message,
            'code': 'ACCESS_EXPIRED'
        }), 403

    # 2. Try fetching actual file bytes (supports local storage and Supabase storage download)
    file_bytes = storage_service.read_pdf_bytes(doc['storage_path'])
    if file_bytes:
        # Record download analytics ONLY when file is confirmed accessible
        db_service.record_download(doc_id, user_id)
        response = send_file(
            io.BytesIO(file_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=doc['file_name']
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{doc["file_name"]}"'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    # 3. If signed URL from Supabase
    signed_url = storage_service.get_signed_url(doc['storage_path'], expires_in_seconds=300)
    if signed_url and not signed_url.startswith('/api/documents/'):
        db_service.record_download(doc_id, user_id)
        return jsonify({
            'download_url': signed_url,
            'file_name': doc['file_name']
        }), 200

    return jsonify({'error': 'Document file is unavailable in storage.'}), 404

@documents_bp.route('/<doc_id>/stream', methods=['GET'])
def stream_document(doc_id):
    """File stream route for in-browser PDF preview / local storage fallback."""
    db_service = current_app.config['DB_SERVICE']
    storage_service = current_app.config['STORAGE_SERVICE']

    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    file_bytes = storage_service.read_pdf_bytes(doc['storage_path'])
    if file_bytes:
        response = send_file(
            io.BytesIO(file_bytes),
            mimetype='application/pdf',
            as_attachment=False,
            download_name=doc['file_name']
        )
        response.headers['Content-Disposition'] = f'inline; filename="{doc["file_name"]}"'
        response.headers['Accept-Ranges'] = 'bytes'
        return response

    signed_url = storage_service.get_signed_url(doc['storage_path'], expires_in_seconds=300)
    if signed_url and not signed_url.startswith('/api/documents/'):
        return redirect(signed_url)

    return jsonify({'error': 'PDF file unavailable.'}), 404

@documents_bp.route('/<doc_id>', methods=['DELETE'])
@login_required
def delete_document(current_user, doc_id):
    user_id = current_user['id']
    role = current_user.get('role', 'student')
    db_service = current_app.config['DB_SERVICE']
    storage_service = current_app.config['STORAGE_SERVICE']

    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    # Allow uploader or admin to delete
    if role != 'admin' and str(doc['uploader_id']) != str(user_id):
        return jsonify({'error': 'Unauthorized to delete this document.'}), 403

    storage_service.delete_document_pdf(doc['storage_path'])
    db_service.delete_document(doc_id)

    return jsonify({'message': 'Document deleted successfully.'}), 200

@documents_bp.route('/<doc_id>/summary', methods=['GET'])
@login_required
def get_document_summary(current_user, doc_id):
    """Checks if a cached AI summary is available for this document."""
    user_id = current_user['id']
    db_service = current_app.config['DB_SERVICE']

    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    # Permission check
    authorized, message = AccessService.authorize_download(db_service, user_id, doc)
    if not authorized:
        return jsonify({'error': message, 'code': 'ACCESS_DENIED'}), 403

    content_hash = doc.get('content_hash')
    cached = db_service.get_cached_summary(doc_id, content_hash) if content_hash else None

    if cached:
        return jsonify({
            'success': True,
            'cached': True,
            'document_id': doc_id,
            'title': doc.get('title'),
            'summary': cached['summary_data'],
            'model': cached.get('model'),
            'created_at': cached.get('created_at')
        }), 200

    return jsonify({
        'success': True,
        'cached': False,
        'document_id': doc_id,
        'summary': None
    }), 200

@documents_bp.route('/<doc_id>/summarize', methods=['POST'])
@login_required
def summarize_document(current_user, doc_id):
    """
    Server-side AI Smart Summarization pipeline:
    1. Authenticates logged-in user and verifies document access permissions.
    2. Checks database summary cache (keyed by document_id and content_hash).
    3. Retrieves stored PDF bytes securely from storage service.
    4. Extracts text and validates text availability (rejecting empty/scanned non-text PDFs).
    5. Dispatches text through chunking/synthesis pipeline to configured AI provider.
    6. Stores generated summary in cache and returns structured 5-section response.
    """
    user_id = current_user['id']
    db_service = current_app.config['DB_SERVICE']
    storage_service = current_app.config['STORAGE_SERVICE']
    ai_service = current_app.config.get('AI_SERVICE')

    if not ai_service:
        return jsonify({'error': 'AI Summarization service is not available.', 'code': 'AI_SERVICE_UNAVAILABLE'}), 503

    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    # 1. Authorization check: logged-in user must have permission to access/download
    authorized, message = AccessService.authorize_download(db_service, user_id, doc)
    if not authorized:
        return jsonify({
            'error': message,
            'code': 'ACCESS_DENIED'
        }), 403

    content_hash = doc.get('content_hash')
    if not content_hash:
        return jsonify({'error': 'Document content fingerprint is missing.', 'code': 'INVALID_METADATA'}), 400

    # 2. Check cached summary in database (avoids repeated API calls)
    force_refresh = request.args.get('refresh', '').lower() in ('true', '1')
    if not force_refresh:
        cached_summary = db_service.get_cached_summary(doc_id, content_hash)
        if cached_summary:
            return jsonify({
                'success': True,
                'cached': True,
                'document_id': doc_id,
                'title': doc.get('title'),
                'summary': cached_summary['summary_data'],
                'model': cached_summary.get('model'),
                'created_at': cached_summary.get('created_at')
            }), 200

    # 3. Retrieve actual stored PDF from storage (NEVER trust frontend path or raw text)
    pdf_bytes = storage_service.read_pdf_bytes(doc['storage_path'])
    if not pdf_bytes:
        return jsonify({'error': 'Document PDF file is unavailable in storage.', 'code': 'FILE_NOT_FOUND'}), 404

    # 4. Generate summary via AIService
    try:
        summary_result = ai_service.summarize_pdf(pdf_bytes, doc_title=doc.get('title', 'Document'))
    except AIServiceError as e:
        return jsonify({'error': e.message, 'code': e.code}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Unexpected summarization error for doc {doc_id}: {e}", exc_info=True)
        return jsonify({'error': f'Failed to generate summary: {str(e)}', 'code': 'SUMMARIZATION_FAILED'}), 500

    # 5. Save to database cache
    saved = db_service.save_cached_summary(
        document_id=doc_id,
        content_hash=content_hash,
        summary_data=summary_result['summary'],
        model=summary_result.get('model', 'gemini-1.5-flash')
    )

    return jsonify({
        'success': True,
        'cached': False,
        'document_id': doc_id,
        'title': doc.get('title'),
        'summary': summary_result['summary'],
        'model': summary_result.get('model'),
        'char_count': summary_result.get('char_count'),
        'page_count': summary_result.get('page_count'),
        'chunks_processed': summary_result.get('chunks_processed', 1),
        'created_at': saved.get('created_at')
    }), 200
