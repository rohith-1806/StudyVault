import os
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.abspath(__file__))
# Load environment files explicitly to prevent CWD dependency issues
load_dotenv(os.path.join(backend_dir, '.env'))
load_dotenv(os.path.join(backend_dir, '..', '.env'))
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'studyvault-super-secret-key-change-in-production')
    
    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # Admin Credentials Defaults (Can be overridden by env)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@studyvault.edu')
    # Default admin password: "AdminPassword123!" hashed with Werkzeug pbkdf2:sha256
    ADMIN_PASSWORD_HASH = os.environ.get(
        'ADMIN_PASSWORD_HASH', 
        'scrypt:32768:8:1$xH2g8l9B4v2k0L5m$95096b79753065a78248bc3bebb0ef3878b273b4b0e50efb0ef7645bfbc094208a0d0d82dd2604ca75a5cb33a6f1947b19818b76db01b1df40003b573510e140'
    )
    
    # Upload limits & Moderation
    MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 25 * 1024 * 1024)) # 25MB
    AUTO_APPROVE = os.environ.get('AUTO_APPROVE', 'true').lower() in ('true', '1', 'yes')
    REWARD_DURATION_HOURS = int(os.environ.get('REWARD_DURATION_HOURS', 24))
    
    # Storage bucket
    STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET', 'documents')
    
    # Local Storage Directory Fallback
    LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage_data')

    # Brevo Transactional Email Configuration
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
    BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', '')
    BREVO_SENDER_NAME = os.environ.get('BREVO_SENDER_NAME', 'StudyVault')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

    # Background Reminder Scheduler
    ENABLE_IN_APP_SCHEDULER = os.environ.get('ENABLE_IN_APP_SCHEDULER', 'true').lower() in ('true', '1', 'yes')
    REMINDER_CHECK_INTERVAL_SECONDS = int(os.environ.get('REMINDER_CHECK_INTERVAL_SECONDS', 60))

    # AI Smart Summarization Configuration
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'gemini').lower()
    AI_API_KEY = os.environ.get('AI_API_KEY') or os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY') or ''
    AI_MODEL = os.environ.get('AI_MODEL') or ('gemini-1.5-flash' if AI_PROVIDER == 'gemini' else 'gpt-4o-mini')
    AI_MOCK = os.environ.get('AI_MOCK', 'false').lower() in ('true', '1', 'yes')
    AI_BASE_URL = os.environ.get('AI_BASE_URL', '')
