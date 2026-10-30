import os
import sqlite3
import uuid
import datetime
import json
from supabase import create_client, Client
from flask import current_app

INITIAL_CATEGORIES = [
    {"id": "cat_1", "name": "B.Tech", "slug": "btech", "description": "Bachelor of Technology core subjects & semester notes", "icon": "GraduationCap"},
    {"id": "cat_2", "name": "M.Tech", "slug": "mtech", "description": "Master of Technology specialization resources", "icon": "BookOpen"},
    {"id": "cat_3", "name": "Engineering", "slug": "engineering", "description": "General Engineering notes, diagrams & lab manuals", "icon": "Cpu"},
    {"id": "cat_4", "name": "Programming", "slug": "programming", "description": "Coding guides, DSA, Java, Python, C++, Web Dev", "icon": "Code"},
    {"id": "cat_5", "name": "Interview Preparation", "slug": "interview-prep", "description": "Technical & HR interview questions & answers", "icon": "Briefcase"},
    {"id": "cat_6", "name": "Placement", "slug": "placement", "description": "Company wise placement papers, drives & syllabus", "icon": "Building"},
    {"id": "cat_7", "name": "Aptitude", "slug": "aptitude", "description": "Quantitative aptitude formulas, shortcuts & practice sets", "icon": "Calculator"},
    {"id": "cat_8", "name": "Reasoning", "slug": "reasoning", "description": "Logical & analytical reasoning question banks", "icon": "Brain"},
    {"id": "cat_9", "name": "Competitive Exams", "slug": "competitive-exams", "description": "GATE, ESE, CAT, GRE & PSU exam prep notes", "icon": "Trophy"},
    {"id": "cat_10", "name": "General Knowledge", "slug": "gk", "description": "Current affairs, general awareness & static GK", "icon": "Globe"},
    {"id": "cat_11", "name": "Skill Development", "slug": "skill-dev", "description": "Cloud, AI/ML, DevOps, UI/UX & Data Analytics", "icon": "Sparkles"},
    {"id": "cat_12", "name": "Project Resources", "slug": "project-resources", "description": "Final year project docs, synopses & viva Q&A", "icon": "FolderKanban"},
    {"id": "cat_13", "name": "Previous Question Papers", "slug": "previous-papers", "description": "Mid-term & university semester PYQs", "icon": "FileText"},
    {"id": "cat_14", "name": "Career Resources", "slug": "career-resources", "description": "Resume templates, cover letters & career guidance", "icon": "UserCheck"},
    {"id": "cat_15", "name": "Other", "slug": "other", "description": "Miscellaneous legitimate student resources", "icon": "Layers"}
]

class DBService:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database.db')
        self._init_sqlite()

    def _get_sqlite_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()

        # Profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                auth_user_id TEXT UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                avatar_url TEXT,
                role TEXT DEFAULT 'student',
                is_active INTEGER DEFAULT 1,
                download_access_started_at TEXT,
                download_access_expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # Categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                icon TEXT,
                created_at TEXT NOT NULL
            )
        ''')

        # Documents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                uploader_id TEXT NOT NULL,
                uploader_name TEXT,
                title TEXT NOT NULL,
                normalized_title TEXT,
                description TEXT,
                category_id TEXT NOT NULL,
                course TEXT,
                subject TEXT,
                semester TEXT,
                tags TEXT,
                storage_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                page_count INTEGER NOT NULL,
                mime_type TEXT DEFAULT 'application/pdf',
                file_hash TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                status TEXT DEFAULT 'pending_review',
                rejection_reason TEXT,
                views_count INTEGER DEFAULT 0,
                downloads_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (uploader_id) REFERENCES profiles (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # Safe Migration: Check if normalized_title column exists in existing database
        cursor.execute("PRAGMA table_info(documents)")
        existing_cols = [c[1] for c in cursor.fetchall()]
        if 'normalized_title' not in existing_cols:
            cursor.execute("ALTER TABLE documents ADD COLUMN normalized_title TEXT")

        # Backfill normalized_title for existing records
        try:
            from services.duplicate_detector import normalize_title
            cursor.execute("SELECT id, title FROM documents WHERE normalized_title IS NULL OR normalized_title = ''")
            unnormalized = cursor.fetchall()
            for doc_row in unnormalized:
                norm = normalize_title(doc_row[1])
                cursor.execute("UPDATE documents SET normalized_title = ? WHERE id = ?", (norm, doc_row[0]))
        except Exception as e:
            print(f"[DBService] Warning during normalized_title backfill: {e}")

        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_category ON documents(category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_uploader ON documents(uploader_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_normalized_title ON documents(normalized_title)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_docs_file_hash_active ON documents(file_hash) WHERE status != "rejected"')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_docs_content_hash ON documents(content_hash)')

        # Downloads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id),
                FOREIGN KEY (user_id) REFERENCES profiles (id)
            )
        ''')

        # Views
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_views (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT,
                created_at TEXT NOT NULL
            )
        ''')

        # Reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                reported_by TEXT NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (id),
                FOREIGN KEY (reported_by) REFERENCES profiles (id)
            )
        ''')

        # Access Grants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_grants (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                source_document_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES profiles (id),
                FOREIGN KEY (source_document_id) REFERENCES documents (id)
            )
        ''')

        # Safe Migration: Check if reminder tracking columns exist in profiles table
        cursor.execute("PRAGMA table_info(profiles)")
        existing_profile_cols = [c[1] for c in cursor.fetchall()]
        if 'reminder_sent_for_expiry' not in existing_profile_cols:
            cursor.execute("ALTER TABLE profiles ADD COLUMN reminder_sent_for_expiry TEXT")
        if 'reminder_sent_at' not in existing_profile_cols:
            cursor.execute("ALTER TABLE profiles ADD COLUMN reminder_sent_at TEXT")

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_reminder ON profiles(download_access_expires_at, reminder_sent_for_expiry)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email)')

        # Email Logs Table for Audit, Delivery Tracking, and Idempotency
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                email_type TEXT NOT NULL,
                recipient TEXT NOT NULL,
                reference_id TEXT,
                message_id TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES profiles (id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_logs_lookup ON email_logs(user_id, email_type, reference_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(email_type, reference_id, status)')

        # Document Summaries Cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_summaries (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                summary_data TEXT NOT NULL,
                model TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_doc_summaries_cache ON document_summaries(document_id, content_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_summaries_lookup ON document_summaries(document_id, content_hash)')

        # Seed categories if empty
        cursor.execute('SELECT COUNT(*) FROM categories')
        if cursor.fetchone()[0] == 0:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for cat in INITIAL_CATEGORIES:
                cursor.execute(
                    'INSERT INTO categories (id, name, slug, description, icon, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (cat['id'], cat['name'], cat['slug'], cat['description'], cat['icon'], now)
                )

        conn.commit()
        conn.close()

    # --- PROFILES ---

    def create_user(self, full_name, email, password_hash, role='student'):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        user_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={user_id}"

        cursor.execute(
            '''INSERT INTO profiles 
               (id, auth_user_id, full_name, email, password_hash, avatar_url, role, is_active, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)''',
            (user_id, user_id, full_name, email, password_hash, avatar, role, now, now)
        )
        conn.commit()
        user = self.get_profile_by_id(user_id)
        conn.close()
        return user

    def get_profile_by_email(self, email):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE LOWER(email) = LOWER(?)', (email.strip(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_profile_by_id(self, user_id):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_user_access_expiry(self, user_id, started_at, expires_at):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            'UPDATE profiles SET download_access_started_at = ?, download_access_expires_at = ?, reminder_sent_for_expiry = NULL, reminder_sent_at = NULL, updated_at = ? WHERE id = ?',
            (started_at, expires_at, now, user_id)
        )
        conn.commit()
        profile = self.get_profile_by_id(user_id)
        conn.close()
        return profile

    def set_user_status(self, user_id, is_active: bool):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute('UPDATE profiles SET is_active = ?, updated_at = ? WHERE id = ?', (1 if is_active else 0, now, user_id))
        conn.commit()
        conn.close()
        return self.get_profile_by_id(user_id)

    def list_all_users(self):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name, email, role, is_active, download_access_expires_at, created_at FROM profiles ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- CATEGORIES ---

    def list_categories(self):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY name ASC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- DOCUMENTS ---

    def create_document(self, doc_data: dict):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        doc_id = doc_data.get('id') or str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        norm_title = doc_data.get('normalized_title')
        if not norm_title:
            from services.duplicate_detector import normalize_title
            norm_title = normalize_title(doc_data['title'])

        cursor.execute(
            '''INSERT INTO documents (
                id, uploader_id, uploader_name, title, normalized_title, description, category_id, course, subject, 
                semester, tags, storage_path, file_name, file_size, page_count, mime_type, 
                file_hash, content_hash, status, rejection_reason, views_count, downloads_count, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)''',
            (
                doc_id, doc_data['uploader_id'], doc_data.get('uploader_name', 'Student'),
                doc_data['title'], norm_title, doc_data.get('description', ''), doc_data['category_id'],
                doc_data.get('course', ''), doc_data.get('subject', ''), doc_data.get('semester', ''),
                doc_data.get('tags', ''), doc_data['storage_path'], doc_data['file_name'],
                doc_data['file_size'], doc_data['page_count'], doc_data.get('mime_type', 'application/pdf'),
                doc_data['file_hash'], doc_data['content_hash'], doc_data.get('status', 'pending_review'),
                doc_data.get('rejection_reason', ''), now, now
            )
        )
        conn.commit()
        doc = self.get_document_by_id(doc_id)
        conn.close()
        return doc

    def find_document_by_file_hash(self, file_hash: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE file_hash = ? AND status != "rejected"', (file_hash,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def find_document_by_normalized_title(self, normalized_title: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE normalized_title = ? AND status != "rejected"', (normalized_title,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def find_document_by_title_normalized(self, norm_title: str):
        """Finds any active document whose title normalizes to norm_title."""
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        # Direct column check
        cursor.execute('SELECT * FROM documents WHERE normalized_title = ? AND status != "rejected"', (norm_title,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

        # Fallback check across all documents in case legacy rows weren't indexed
        from services.duplicate_detector import normalize_title
        cursor.execute('SELECT * FROM documents WHERE status != "rejected"')
        all_docs = cursor.fetchall()
        for d in all_docs:
            if normalize_title(d['title']) == norm_title:
                conn.close()
                return dict(d)

        conn.close()
        return None

    def find_legacy_document_by_file_hash(self, target_hash: str, storage_service):
        """Checks existing legacy documents with missing file_hash against their stored PDF bytes."""
        import hashlib
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE (file_hash IS NULL OR file_hash = "") AND status != "rejected"')
        legacy_rows = cursor.fetchall()
        for row in legacy_rows:
            doc = dict(row)
            try:
                pdf_bytes = storage_service.read_pdf_bytes(doc['storage_path'])
                if pdf_bytes:
                    h = hashlib.sha256(pdf_bytes).hexdigest()
                    cursor.execute('UPDATE documents SET file_hash = ? WHERE id = ?', (h, doc['id']))
                    conn.commit()
                    if h == target_hash:
                        conn.close()
                        doc['file_hash'] = h
                        return doc
            except Exception as e:
                print(f"[DBService] Warning reading legacy doc {doc['id']}: {e}")
        conn.close()
        return None

    def backfill_legacy_hashes(self, storage_service):
        """Backfills missing SHA-256 hashes for legacy documents from storage."""
        import hashlib
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE (file_hash IS NULL OR file_hash = "") AND status != "rejected"')
        rows = cursor.fetchall()
        for row in rows:
            doc_id = row['id']
            storage_path = row['storage_path']
            try:
                pdf_bytes = storage_service.read_pdf_bytes(storage_path)
                if pdf_bytes:
                    h = hashlib.sha256(pdf_bytes).hexdigest()
                    cursor.execute('UPDATE documents SET file_hash = ? WHERE id = ?', (h, doc_id))
            except Exception as e:
                print(f"[DBService] Warning: Could not backfill hash for {doc_id}: {e}")
        conn.commit()
        conn.close()

    def find_document_by_content_hash(self, content_hash: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE content_hash = ? AND status != "rejected"', (content_hash,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_document_by_id(self, doc_id: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, c.name as category_name, c.slug as category_slug
            FROM documents d
            LEFT JOIN categories c ON d.category_id = c.id
            WHERE d.id = ?
        ''', (doc_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_documents(self, category_id=None, search=None, course=None, status='approved', sort_by='latest', limit=50, offset=0):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()

        query = '''
            SELECT d.*, c.name as category_name, c.slug as category_slug
            FROM documents d
            LEFT JOIN categories c ON d.category_id = c.id
            WHERE 1=1
        '''
        params = []

        if status:
            query += ' AND d.status = ?'
            params.append(status)

        if category_id:
            query += ' AND (d.category_id = ? OR c.slug = ?)'
            params.extend([category_id, category_id])

        if course:
            query += ' AND LOWER(d.course) LIKE ?'
            params.append(f"%{course.lower()}%")

        if search:
            cleaned_search = search.strip()
            words = [w.strip() for w in cleaned_search.split() if w.strip()]
            if words:
                word_clauses = []
                for w in words:
                    term = f"%{w.lower()}%"
                    word_clauses.append(''' (
                        LOWER(d.title) LIKE ? OR 
                        LOWER(d.description) LIKE ? OR 
                        LOWER(d.subject) LIKE ? OR 
                        LOWER(d.tags) LIKE ? OR 
                        LOWER(d.course) LIKE ? OR 
                        LOWER(c.name) LIKE ?
                    ) ''')
                    params.extend([term, term, term, term, term, term])
                query += ' AND (' + ' OR '.join(word_clauses) + ')'

        # Sorting
        if sort_by == 'popular':
            query += ' ORDER BY d.views_count DESC, d.created_at DESC'
        elif sort_by == 'downloads':
            query += ' ORDER BY d.downloads_count DESC, d.created_at DESC'
        else:
            query += ' ORDER BY d.created_at DESC'

        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        documents = [dict(r) for r in rows]

        if search and search.strip():
            q = search.strip().lower()
            words = [w.strip() for w in q.split() if w.strip()]
            if words:
                scored = []
                for doc in documents:
                    title = (doc.get('title') or '').lower()
                    subject = (doc.get('subject') or '').lower()
                    course_val = (doc.get('course') or '').lower()
                    desc = (doc.get('description') or '').lower()
                    tags = (doc.get('tags') or '').lower()
                    all_fields = [title, subject, course_val, desc, tags]

                    # 1. Exact phrase match
                    if title == q or subject == q:
                        score = 100
                    elif any(q in f for f in [title, subject]):
                        score = 90
                    elif any(q in f for f in all_fields):
                        score = 80
                    else:
                        matched_words = [w for w in words if any(w in f for f in all_fields)]
                        if not matched_words:
                            score = 0
                        else:
                            score = (len(matched_words) / len(words)) * 70

                    if score > 0:
                        scored.append((doc, score))

                if not scored:
                    return []

                max_score = max(s for _, s in scored)
                if max_score >= 80:
                    threshold = 60
                else:
                    threshold = max(35, max_score * 0.7)

                documents = [d for d, s in scored if s >= threshold]

        return documents

    def list_user_contributions(self, user_id: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, c.name as category_name
            FROM documents d
            LEFT JOIN categories c ON d.category_id = c.id
            WHERE d.uploader_id = ?
            ORDER BY d.created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_document_status(self, doc_id: str, status: str, rejection_reason: str = ''):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            'UPDATE documents SET status = ?, rejection_reason = ?, updated_at = ? WHERE id = ?',
            (status, rejection_reason, now, doc_id)
        )
        conn.commit()
        doc = self.get_document_by_id(doc_id)
        conn.close()
        return doc

    def delete_document(self, doc_id: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM document_summaries WHERE document_id = ?', (doc_id,))
        cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        conn.commit()
        conn.close()
        return True

    def increment_views(self, doc_id: str, user_id: str = None) -> int:
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        view_id = str(uuid.uuid4())

        cursor.execute('INSERT INTO document_views (id, document_id, user_id, created_at) VALUES (?, ?, ?, ?)',
                       (view_id, doc_id, user_id, now))
        cursor.execute('UPDATE documents SET views_count = views_count + 1 WHERE id = ?', (doc_id,))
        conn.commit()

        cursor.execute('SELECT views_count FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        updated_count = row['views_count'] if row else 1
        conn.close()
        return updated_count

    def record_download(self, doc_id: str, user_id: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        dl_id = str(uuid.uuid4())

        cursor.execute('INSERT INTO downloads (id, document_id, user_id, created_at) VALUES (?, ?, ?, ?)',
                       (dl_id, doc_id, user_id, now))
        cursor.execute('UPDATE documents SET downloads_count = downloads_count + 1 WHERE id = ?', (doc_id,))
        conn.commit()
        conn.close()

    # --- REPORTS ---

    def create_report(self, doc_id: str, user_id: str, reason: str, description: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        report_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute('''
            INSERT INTO reports (id, document_id, reported_by, reason, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'open', ?)
        ''', (report_id, doc_id, user_id, reason, description, now))
        conn.commit()
        conn.close()
        return report_id

    def list_reports(self, status=None):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        query = '''
            SELECT r.*, d.title as document_title, p.full_name as reporter_name, p.email as reporter_email
            FROM reports r
            LEFT JOIN documents d ON r.document_id = d.id
            LEFT JOIN profiles p ON r.reported_by = p.id
        '''
        params = []
        if status:
            query += ' WHERE r.status = ?'
            params.append(status)
        query += ' ORDER BY r.created_at DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_report_status(self, report_id: str, status: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute('UPDATE reports SET status = ?, resolved_at = ? WHERE id = ?', (status, now, report_id))
        conn.commit()
        conn.close()

    # --- ACCESS GRANTS ---

    def create_access_grant(self, user_id: str, source_document_id: str, started_at: str, expires_at: str):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        grant_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute('''
            INSERT INTO access_grants (id, user_id, source_document_id, started_at, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (grant_id, user_id, source_document_id, started_at, expires_at, now))
        conn.commit()
        conn.close()
        return grant_id

    # --- ADMIN STATS ---

    def get_admin_dashboard_stats(self):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM profiles WHERE role = "student"')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM documents')
        total_documents = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM documents WHERE status = "approved"')
        approved_documents = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM documents WHERE status = "pending_review"')
        pending_documents = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM documents WHERE status = "rejected"')
        rejected_documents = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM downloads')
        total_downloads = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM document_views')
        total_views = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT uploader_id) FROM documents WHERE status = "approved"')
        active_contributors = cursor.fetchone()[0]

        conn.close()
        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "approved_documents": approved_documents,
            "pending_documents": pending_documents,
            "rejected_documents": rejected_documents,
            "total_downloads": total_downloads,
            "total_views": total_views,
            "active_contributors": active_contributors
        }

    # --- EMAIL & REMINDER HELPERS ---

    def log_email(self, user_id: str, email_type: str, recipient: str, reference_id: str = None, status: str = 'sent', message_id: str = None, error_message: str = None) -> str:
        """Records an email delivery or attempt in email_logs for auditing and idempotency tracking."""
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        log_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            '''INSERT INTO email_logs 
               (id, user_id, email_type, recipient, reference_id, message_id, status, error_message, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (log_id, user_id, email_type, recipient.strip().lower(), reference_id, message_id, status, error_message, now)
        )
        conn.commit()
        conn.close()
        return log_id

    def has_email_been_sent(self, email_type: str, reference_id: str) -> bool:
        """Checks if a successful email with this type and reference ID has already been recorded."""
        if not reference_id:
            return False
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM email_logs WHERE email_type = ? AND reference_id = ? AND status = "sent" LIMIT 1',
            (email_type, str(reference_id))
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def get_eligible_reminder_users(self, threshold_seconds: int = 10 * 3600) -> list:
        """
        Finds active users whose access period has not expired, has approximately threshold_seconds
        (default 10 hours) or less remaining, and who have not already received the reminder
        for this specific access period.
        """
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()

        cursor.execute(
            '''SELECT id, full_name, email, role, is_active, 
                      download_access_started_at, download_access_expires_at, 
                      reminder_sent_for_expiry, reminder_sent_at
               FROM profiles 
               WHERE is_active = 1 
                 AND download_access_expires_at IS NOT NULL 
                 AND download_access_expires_at > ?
                 AND (reminder_sent_for_expiry IS NULL OR reminder_sent_for_expiry != download_access_expires_at)''',
            (now_iso,)
        )
        rows = cursor.fetchall()
        conn.close()

        eligible = []
        for r in rows:
            u = dict(r)
            exp_str = u.get('download_access_expires_at')
            if not exp_str:
                continue
            try:
                exp_dt = datetime.datetime.fromisoformat(exp_str.replace('Z', '+00:00'))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=datetime.timezone.utc)
                remaining = (exp_dt - now).total_seconds()
                # Must be active (remaining > 0) and within 10 hours (remaining <= threshold_seconds)
                if 0 < remaining <= threshold_seconds:
                    u['remaining_seconds'] = int(remaining)
                    eligible.append(u)
            except Exception as ex:
                print(f"[DBService] Error parsing expiry for user {u.get('id')}: {ex}")
                continue

        return eligible

    def claim_reminder_for_user(self, user_id: str, expires_at: str) -> bool:
        """
        Atomically claims a reminder for a user and specific access period.
        Returns True if this caller successfully claimed the reminder, False if another worker claimed it first.
        """
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            '''UPDATE profiles 
               SET reminder_sent_for_expiry = ?, reminder_sent_at = ?, updated_at = ?
               WHERE id = ? 
                 AND download_access_expires_at = ?
                 AND (reminder_sent_for_expiry IS NULL OR reminder_sent_for_expiry != ?)''',
            (expires_at, now_iso, now_iso, user_id, expires_at, expires_at)
        )
        claimed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return claimed

    def reset_failed_reminder_claim(self, user_id: str, expires_at: str):
        """Allows resetting a reminder claim if sending encountered an unexpected transient network error."""
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            '''UPDATE profiles 
               SET reminder_sent_for_expiry = NULL, reminder_sent_at = NULL, updated_at = ?
               WHERE id = ? AND download_access_expires_at = ? AND reminder_sent_for_expiry = ?''',
            (now_iso, user_id, expires_at, expires_at)
        )
        conn.commit()
        conn.close()

    def get_recent_email_logs(self, limit: int = 50) -> list:
        """Retrieves recent email audit logs."""
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM email_logs ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- DOCUMENT SUMMARIES CACHE ---

    def get_cached_summary(self, document_id: str, content_hash: str) -> dict | None:
        """Retrieves cached AI summary if it matches the current document content hash."""
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM document_summaries WHERE document_id = ? AND content_hash = ? LIMIT 1',
            (document_id, content_hash)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        res = dict(row)
        try:
            res['summary_data'] = json.loads(res['summary_data'])
        except Exception:
            pass
        return res

    def save_cached_summary(self, document_id: str, content_hash: str, summary_data: dict | str, model: str = None) -> dict:
        """Saves or updates cached AI summary keyed by document_id and content_hash."""
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        summary_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        serialized_data = json.dumps(summary_data) if isinstance(summary_data, (dict, list)) else str(summary_data)

        cursor.execute(
            '''INSERT INTO document_summaries (id, document_id, content_hash, summary_data, model, created_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(document_id, content_hash) 
               DO UPDATE SET summary_data = excluded.summary_data, model = excluded.model, created_at = excluded.created_at''',
            (summary_id, document_id, content_hash, serialized_data, model, now)
        )
        conn.commit()
        conn.close()
        return {
            "id": summary_id,
            "document_id": document_id,
            "content_hash": content_hash,
            "summary_data": summary_data,
            "model": model,
            "created_at": now
        }

    def delete_cached_summary(self, document_id: str):
        """Invalidates all cached summaries for a document."""
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM document_summaries WHERE document_id = ?', (document_id,))
        conn.commit()
        conn.close()
