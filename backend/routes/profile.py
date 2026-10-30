from flask import Blueprint, jsonify, current_app
from utils.security import login_required
from services.access_service import AccessService

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

def calculate_contribution_level(approved_count: int) -> dict:
    if approved_count >= 20:
        return {"level": "🏆 Top Contributor", "badge": "Gold", "min_docs": 20}
    elif approved_count >= 10:
        return {"level": "⭐ Knowledge Contributor", "badge": "Silver", "min_docs": 10}
    elif approved_count >= 3:
        return {"level": "📚 Active Contributor", "badge": "Bronze", "min_docs": 3}
    else:
        return {"level": "🌱 New Contributor", "badge": "Starter", "min_docs": 0}

@profile_bp.route('', methods=['GET'])
@login_required
def get_profile(current_user):
    user_id = current_user['id']
    db_service = current_app.config['DB_SERVICE']
    
    user = db_service.get_profile_by_id(user_id)
    if not user:
        return jsonify({'error': 'Profile not found.'}), 404

    contributions = db_service.list_user_contributions(user_id)
    approved_count = sum(1 for c in contributions if c.get('status') == 'approved')
    total_views = sum(c.get('views_count', 0) for c in contributions)
    total_downloads = sum(c.get('downloads_count', 0) for c in contributions)

    level_info = calculate_contribution_level(approved_count)
    access_active = AccessService.is_access_active(user)
    remaining_seconds = AccessService.get_remaining_access_seconds(user)

    return jsonify({
        'profile': {
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'avatar_url': user['avatar_url'],
            'role': user['role'],
            'created_at': user['created_at'],
            'access_active': access_active,
            'remaining_seconds': remaining_seconds,
            'access_started_at': user.get('download_access_started_at'),
            'access_expires_at': user.get('download_access_expires_at'),
            'total_uploads': len(contributions),
            'approved_uploads': approved_count,
            'total_views': total_views,
            'total_downloads': total_downloads,
            'contribution_level': level_info['level'],
            'badge': level_info['badge']
        }
    }), 200

@profile_bp.route('/contributions', methods=['GET'])
@login_required
def get_contributions(current_user):
    user_id = current_user['id']
    db_service = current_app.config['DB_SERVICE']
    
    contributions = db_service.list_user_contributions(user_id)
    return jsonify({
        'contributions': contributions,
        'count': len(contributions)
    }), 200
