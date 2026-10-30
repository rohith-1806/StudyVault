import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import PdfViewerModal from './components/PdfViewerModal';
import DocumentSummaryModal from './components/DocumentSummaryModal';
import LandingHome from './pages/LandingHome';
import Login from './pages/Login';
import Register from './pages/Register';
import DigitalLibrary from './pages/DigitalLibrary';
import DocumentDetails from './pages/DocumentDetails';
import UploadDocument from './pages/UploadDocument';
import UserProfile from './pages/UserProfile';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import CustomCursor from './components/CustomCursor';
import { api } from './services/api';
import { FaLock, FaClock, FaCloudUploadAlt, FaTimes } from 'react-icons/fa';

function AppContent() {
  const { user } = useAuth();
  const [currentPath, setCurrentPath] = useState(window.location.pathname + window.location.search);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [summaryDoc, setSummaryDoc] = useState(null);
  const [accessExpiredModalOpen, setAccessExpiredModalOpen] = useState(false);

  // Router navigation helper
  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname + window.location.search);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleDownload = async (doc) => {
    if (!user) {
      navigate('/login');
      return;
    }
    try {
      const res = await api.downloadDocument(doc.id);
      if (res.type === 'blob') {
        const url = window.URL.createObjectURL(res.blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = res.fileName || doc.file_name || `${doc.title}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => window.URL.revokeObjectURL(url), 10000);
      } else if (res.download_url) {
        const a = document.createElement('a');
        a.href = res.download_url;
        a.download = res.file_name || doc.file_name || `${doc.title}.pdf`;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    } catch (err) {
      if (err.code === 'ACCESS_EXPIRED' || err.status === 403) {
        setAccessExpiredModalOpen(true);
      } else {
        alert(err.message || 'Download failed.');
      }
    }
  };

  const handlePreview = (doc) => {
    setPreviewDoc(doc);
  };

  const handleOpenSummary = (doc) => {
    setSummaryDoc(doc);
  };

  const handleViewRecorded = (docId, newCount) => {
    setPreviewDoc(prev => (prev && prev.id === docId ? { ...prev, views_count: newCount } : prev));
    window.dispatchEvent(new CustomEvent('studyvault:doc-view-updated', {
      detail: { docId, viewsCount: newCount }
    }));
  };

  // Extract pathname and query parameters
  const pathname = currentPath.split('?')[0];
  const qIndex = currentPath.indexOf('?');
  const searchString = qIndex !== -1 ? currentPath.slice(qIndex) : window.location.search;
  const searchParams = new URLSearchParams(searchString);
  const initialSearch = searchParams.get('search') || '';
  const initialCategory = searchParams.get('category') || '';

  // Route matcher
  const renderRoute = () => {
    if (pathname === '/') {
      return <LandingHome navigate={navigate} onPreview={handlePreview} onDownload={handleDownload} />;
    }
    if (pathname === '/login') {
      return <Login navigate={navigate} />;
    }
    if (pathname === '/register') {
      return <Register navigate={navigate} />;
    }
    if (pathname === '/library') {
      return (
        <DigitalLibrary
          key={currentPath}
          initialSearch={initialSearch}
          initialCategory={initialCategory}
          navigate={navigate}
          onPreview={handlePreview}
          onDownload={handleDownload}
          onOpenSummary={handleOpenSummary}
        />
      );
    }
    if (pathname.startsWith('/document/')) {
      const docId = pathname.split('/document/')[1];
      return (
        <DocumentDetails
          docId={docId}
          navigate={navigate}
          onPreview={handlePreview}
          onDownload={handleDownload}
          onOpenSummary={handleOpenSummary}
        />
      );
    }
    if (pathname === '/upload') {
      return <UploadDocument navigate={navigate} />;
    }
    if (pathname === '/profile') {
      return <UserProfile navigate={navigate} onPreview={handlePreview} />;
    }
    if (pathname === '/admin/login') {
      return <AdminLogin navigate={navigate} />;
    }
    if (pathname.startsWith('/admin')) {
      return <AdminDashboard navigate={navigate} onPreview={handlePreview} />;
    }

    // Default 404 - only on truly invalid routes
    return (
      <div className="max-w-md mx-auto py-20 text-center glass-card p-8 space-y-4 my-12">
        <h2 className="text-4xl font-black">404</h2>
        <p className="text-xs text-slate-400 font-medium">The page you requested could not be found.</p>
        <button onClick={() => navigate('/')} className="glass-btn-primary px-6 py-2.5 text-xs font-bold">
          Go to Home
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-page)] text-[var(--text-primary)] selection:bg-violet-500 selection:text-white relative transition-colors duration-200">
      <CustomCursor />
      
      <Navbar currentPath={pathname} navigate={navigate} />

      <main className="flex-1 z-10">
        {renderRoute()}
      </main>

      <Footer navigate={navigate} />

      {/* PDF IN-BROWSER PREVIEW MODAL */}
      {previewDoc && (
        <PdfViewerModal
          doc={previewDoc}
          onClose={() => setPreviewDoc(null)}
          onDownload={handleDownload}
          onViewRecorded={handleViewRecorded}
          onOpenSummary={handleOpenSummary}
        />
      )}

      {/* AI SMART SUMMARY MODAL */}
      {summaryDoc && (
        <DocumentSummaryModal
          doc={summaryDoc}
          onClose={() => setSummaryDoc(null)}
          onDownload={handleDownload}
          navigate={navigate}
        />
      )}

      {/* ACCESS EXPIRED EXPLANATION MODAL */}
      {accessExpiredModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="glass-modal w-full max-w-md p-8 relative text-center space-y-5">
            <button
              onClick={() => setAccessExpiredModalOpen(false)}
              className="absolute top-4 right-4 glass-btn p-2 text-slate-400 hover:text-red-400 rounded-xl"
            >
              <FaTimes className="w-4 h-4" />
            </button>

            <div className="w-16 h-16 glass-pressed text-amber-400 mx-auto flex items-center justify-center rounded-full border border-amber-500/30">
              <FaLock className="w-7 h-7 text-amber-400" />
            </div>

            <div>
              <h3 className="text-xl font-black">24-Hour Access Expired</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Your free download access has expired. Upload one valid study document to unlock <strong className="text-emerald-400">24 hours of unlimited downloads</strong>.
              </p>
            </div>

            <div className="glass-pressed p-4 rounded-2xl text-xs font-bold flex items-center gap-2 text-left border border-white/10">
              <FaClock className="w-5 h-5 text-violet-400 flex-shrink-0" />
              <span>You can always download your own uploaded documents for free anytime!</span>
            </div>

            <div className="pt-2 flex flex-col gap-2">
              <button
                onClick={() => {
                  setAccessExpiredModalOpen(false);
                  navigate('/upload');
                }}
                className="w-full glass-btn-primary py-3.5 text-xs font-bold flex items-center justify-center gap-2"
              >
                <FaCloudUploadAlt className="w-4 h-4" /> Upload Document to Unlock Access
              </button>
              <button
                onClick={() => setAccessExpiredModalOpen(false)}
                className="w-full glass-btn py-2.5 text-xs font-bold text-slate-400"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}
