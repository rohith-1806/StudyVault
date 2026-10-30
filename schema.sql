-- ====================================================================
-- STUDYVAULT STUDENT DIGITAL LIBRARY PLATFORM
-- SUPABASE POSTGRESQL DATABASE SCHEMA & ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PROFILES TABLE
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar_url TEXT,
    role TEXT DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    download_access_started_at TIMESTAMPTZ,
    download_access_expires_at TIMESTAMPTZ,
    reminder_sent_for_expiry TIMESTAMPTZ,
    reminder_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. CATEGORIES TABLE
CREATE TABLE IF NOT EXISTS public.categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. DOCUMENTS TABLE
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploader_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    uploader_name TEXT,
    title TEXT NOT NULL,
    normalized_title TEXT,
    description TEXT,
    category_id TEXT NOT NULL REFERENCES public.categories(id),
    course TEXT,
    subject TEXT,
    semester TEXT,
    tags TEXT,
    storage_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    page_count INT NOT NULL,
    mime_type TEXT DEFAULT 'application/pdf',
    file_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT DEFAULT 'pending_review' CHECK (status IN ('approved', 'pending_review', 'rejected')),
    rejection_reason TEXT,
    views_count INT DEFAULT 0,
    downloads_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. DOWNLOADS ANALYTICS TABLE
CREATE TABLE IF NOT EXISTS public.downloads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. DOCUMENT VIEWS ANALYTICS TABLE
CREATE TABLE IF NOT EXISTS public.document_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. REPORTS TABLE
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    reported_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'reviewing', 'resolved', 'dismissed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 7. ACCESS GRANTS AUDIT LOG TABLE
CREATE TABLE IF NOT EXISTS public.access_grants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    source_document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. DOCUMENT SUMMARIES CACHE TABLE
CREATE TABLE IF NOT EXISTS public.document_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    content_hash TEXT NOT NULL,
    summary_data JSONB NOT NULL,
    model TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_document_summary UNIQUE (document_id, content_hash)
);

CREATE TABLE IF NOT EXISTS public.email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    email_type TEXT NOT NULL,
    recipient TEXT NOT NULL,
    reference_id TEXT,
    message_id TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- PERFORMANCE INDEXES
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_category_id ON public.documents(category_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploader_id ON public.documents(uploader_id);
CREATE INDEX IF NOT EXISTS idx_documents_normalized_title ON public.documents(normalized_title);
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_file_hash_active ON public.documents(file_hash) WHERE status != 'rejected';
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON public.documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON public.documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON public.documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_downloads_count ON public.documents(downloads_count DESC);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_reminder ON public.profiles(download_access_expires_at, reminder_sent_for_expiry);
CREATE INDEX IF NOT EXISTS idx_email_logs_lookup ON public.email_logs(user_id, email_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON public.email_logs(email_type, reference_id, status);
CREATE INDEX IF NOT EXISTS idx_doc_summaries_lookup ON public.document_summaries(document_id, content_hash);

-- Full text search index
CREATE INDEX IF NOT EXISTS idx_documents_fts ON public.documents 
USING gin(to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'') || ' ' || coalesce(subject,'') || ' ' || coalesce(course,'') || ' ' || coalesce(tags,'')));

-- ====================================================================
-- SEED DATA: INITIAL CATEGORIES
-- ====================================================================
INSERT INTO public.categories (id, name, slug, description, icon) VALUES
('cat_1', 'B.Tech', 'btech', 'Bachelor of Technology core subjects & semester notes', 'GraduationCap'),
('cat_2', 'M.Tech', 'mtech', 'Master of Technology specialization resources', 'BookOpen'),
('cat_3', 'Engineering', 'engineering', 'General Engineering notes, diagrams & lab manuals', 'Cpu'),
('cat_4', 'Programming', 'programming', 'Coding guides, DSA, Java, Python, C++, Web Dev', 'Code'),
('cat_5', 'Interview Preparation', 'interview-prep', 'Technical & HR interview questions & answers', 'Briefcase'),
('cat_6', 'Placement', 'placement', 'Company wise placement papers, drives & syllabus', 'Building'),
('cat_7', 'Aptitude', 'aptitude', 'Quantitative aptitude formulas, shortcuts & practice sets', 'Calculator'),
('cat_8', 'Reasoning', 'reasoning', 'Logical & analytical reasoning question banks', 'Brain'),
('cat_9', 'Competitive Exams', 'competitive-exams', 'GATE, ESE, CAT, GRE & PSU exam prep notes', 'Trophy'),
('cat_10', 'General Knowledge', 'gk', 'Current affairs, general awareness & static GK', 'Globe'),
('cat_11', 'Skill Development', 'skill-dev', 'Cloud, AI/ML, DevOps, UI/UX & Data Analytics', 'Sparkles'),
('cat_12', 'Project Resources', 'project-resources', 'Final year project docs, synopses & viva Q&A', 'FolderKanban'),
('cat_13', 'Previous Question Papers', 'previous-papers', 'Mid-term & university semester PYQs', 'FileText'),
('cat_14', 'Career Resources', 'career-resources', 'Resume templates, cover letters & career guidance', 'UserCheck'),
('cat_15', 'Other', 'other', 'Miscellaneous legitimate student resources', 'Layers')
ON CONFLICT (id) DO NOTHING;

-- ====================================================================
-- SUPABASE ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.downloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.access_grants ENABLE ROW LEVEL SECURITY;

-- Categories: Anyone can read
CREATE POLICY "Categories are readable by everyone" ON public.categories
    FOR SELECT USING (true);

-- Profiles: Users can read public profile details, write own profile
CREATE POLICY "Profiles readable by authenticated users" ON public.profiles
    FOR SELECT USING (true);

-- Documents: Public can read approved documents, uploader can read own, admin can read all
CREATE POLICY "Approved documents readable by everyone" ON public.documents
    FOR SELECT USING (status = 'approved' OR auth.uid() = uploader_id);

-- Admin full management policy handled via Supabase Service Role Key inside Flask backend
