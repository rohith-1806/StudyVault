import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from services.db_service import DBService
from services.storage_service import StorageService

def create_app(config_class=Config):
    dist_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'))
    app = Flask(__name__, static_folder=dist_folder, static_url_path='')
    app.config.from_object(config_class)

    # Configure Production CORS
    frontend_url = os.environ.get('FRONTEND_URL', '*')
    cors_origins = [origin.strip() for origin in frontend_url.split(',') if origin.strip()]
    if '*' in cors_origins or not cors_origins:
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

    # Initialize Services
    db_service = DBService()
    storage_service = StorageService()
    from services.email_service import EmailService
    email_service = EmailService(
        api_key=app.config.get('BREVO_API_KEY'),
        sender_email=app.config.get('BREVO_SENDER_EMAIL'),
        sender_name=app.config.get('BREVO_SENDER_NAME', 'StudyVault'),
        frontend_url=app.config.get('FRONTEND_URL', 'http://localhost:5173'),
        db_service=db_service
    )

    from services.ai_service import AIService
    ai_service = AIService(
        api_key=app.config.get('AI_API_KEY'),
        provider=app.config.get('AI_PROVIDER', 'gemini'),
        model=app.config.get('AI_MODEL'),
        mock=app.config.get('AI_MOCK', False) or app.config.get('TESTING', False),
        base_url=app.config.get('AI_BASE_URL')
    )

    app.config['DB_SERVICE'] = db_service
    app.config['STORAGE_SERVICE'] = storage_service
    app.config['EMAIL_SERVICE'] = email_service
    app.config['AI_SERVICE'] = ai_service

    # Optional In-App Background Reminder Scheduler (for single-process local dev)
    if app.config.get('ENABLE_IN_APP_SCHEDULER', False) and not app.config.get('TESTING', False):
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from services.reminder_service import ReminderService
                import atexit

                reminder_svc = ReminderService(db_service=db_service, email_service=email_service)
                interval_secs = app.config.get('REMINDER_CHECK_INTERVAL_SECONDS', 60)

                scheduler = BackgroundScheduler(daemon=True)
                scheduler.add_job(
                    func=reminder_svc.check_and_send_reminders,
                    trigger="interval",
                    seconds=interval_secs,
                    id="10h_access_reminder_job",
                    replace_existing=True
                )
                scheduler.start()
                app.config['REMINDER_SCHEDULER'] = scheduler
                atexit.register(lambda: scheduler.shutdown(wait=False))
            except Exception as e:
                print(f"[Scheduler] In-app scheduler initialization note: {e}")

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.documents import documents_bp
    from routes.profile import profile_bp
    from routes.reports import reports_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'app': 'StudyVault Student Digital Library API',
            'version': '1.0.0'
        }), 200

    # SPA Fallback for Frontend Single Page Application
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path.startswith('api/'):
            return jsonify({'error': 'Endpoint not found.'}), 404
        file_path = os.path.join(dist_folder, path)
        if path != '' and os.path.exists(file_path):
            return send_from_directory(dist_folder, path)
        return send_from_directory(dist_folder, 'index.html')

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'An internal server error occurred.'}), 500

    return app
# StudyVault AI Smart Summarization integrated
