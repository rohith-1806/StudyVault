from flask import Blueprint, request, jsonify, current_app
from utils.security import login_required

reports_bp = Blueprint('reports', __name__, url_prefix='/api/documents')

VALID_REASONS = [
    'copyright_issue',
    'wrong_content',
    'spam',
    'malware_suspicious',
    'misleading_title',
    'duplicate',
    'inappropriate_content',
    'other'
]

@reports_bp.route('/<doc_id>/report', methods=['POST'])
@login_required
def report_document(current_user, doc_id):
    user_id = current_user['id']
    data = request.get_json() or {}
    reason = data.get('reason', '').strip()
    description = data.get('description', '').strip()

    if not reason or reason not in VALID_REASONS:
        return jsonify({'error': 'Please select a valid report reason.'}), 400

    db_service = current_app.config['DB_SERVICE']
    doc = db_service.get_document_by_id(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    report_id = db_service.create_report(doc_id=doc_id, user_id=user_id, reason=reason, description=description)

    return jsonify({
        'message': 'Report submitted successfully. Thank you for keeping the library safe.',
        'report_id': report_id
    }), 201
