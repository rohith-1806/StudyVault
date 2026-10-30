import React, { useState, useEffect } from 'react';
import { 
  FaFilePdf, 
  FaEye, 
  FaDownload, 
  FaUser, 
  FaCalendarAlt, 
  FaTag, 
  FaHdd, 
  FaFlag, 
  FaShareAlt, 
  FaLock, 
  FaCheckCircle, 
  FaArrowLeft,
  FaBookOpen
} from 'react-icons/fa';
import { api } from '../services/api';
import { formatFileSize } from '../components/DocumentCard';
import ReportModal from '../components/ReportModal';

export default function DocumentDetails({ docId, navigate, onPreview, onDownload, onOpenSummary }) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function fetchDoc() {
      setLoading(true);
      try {
        const res = await api.getDocument(docId);
        setDoc(res.document);
      } catch (err) {
        setError(err.message || 'Failed to load document.');
      } finally {
        setLoading(false);
      }
    }
    if (docId) fetchDoc();
  }, [docId]);

  useEffect(() => {
    const handleDocViewUpdate = (e) => {
      const { docId: updatedId, viewsCount } = e.detail || {};
      if (updatedId && String(updatedId) === String(docId)) {
        setDoc(prev => (prev ? { ...prev, views_count: viewsCount } : prev));
      }
    };
    window.addEventListener('studyvault:doc-view-updated', handleDocViewUpdate);
    return () => window.removeEventListener('studyvault:doc-view-updated', handleDocViewUpdate);
  }, [docId]);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 glass-card p-10 animate-pulse space-y-6">
        <div className="w-32 h-6 bg-slate-700/60 rounded" />
        <div className="w-3/4 h-8 bg-slate-700/60 rounded" />
        <div className="w-full h-40 bg-slate-800/60 rounded" />
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="max-w-md mx-auto py-16 text-center glass-card p-8">
        <FaBookOpen className="w-12 h-12 text-slate-500 mx-auto mb-3" />
        <h3 className="font-bold text-white text-base">{error || 'Document not found.'}</h3>
        <button onClick={() => navigate('/library')} className="glass-btn px-4 py-2 text-xs font-bold text-violet-400 mt-4">
          Back to Library
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-8 py-8 space-y-6">
      
      {/* BACK NAVIGATION */}
      <button
        onClick={() => navigate('/library')}
        className="glass-btn px-4 py-2 text-xs font-bold text-slate-300 hover:text-white flex items-center gap-1.5"
      >
        <FaArrowLeft className="w-3.5 h-3.5" /> Back to Digital Library
      </button>

      {/* DOCUMENT HEADER CARD */}
      <div className="glass-card p-6 sm:p-8 space-y-6 border border-white/20">
        
        <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-16 h-20 rounded-2xl bg-gradient-to-br from-violet-600 via-indigo-600 to-cyan-500 p-0.5 shadow-xl shadow-violet-500/20 flex-shrink-0 flex items-center justify-center text-red-400">
              <FaFilePdf className="w-9 h-9" />
            </div>
            <div>
              <span className="glass-chip px-3 py-1 text-xs font-bold text-violet-300 bg-violet-500/20 border-violet-500/30">
                {doc.category_name || 'Study Material'}
              </span>
              <h1 className="text-2xl font-black text-white mt-2 leading-tight">{doc.title}</h1>
              <p className="text-xs text-slate-300 font-medium mt-1">
                Subject: <strong className="text-white">{doc.subject || 'General'}</strong> • Course: {doc.course || 'N/A'} {doc.semester ? `(${doc.semester})` : ''}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={handleShare}
              className="glass-btn px-3 py-2 text-xs font-bold text-slate-300 hover:text-white flex items-center gap-1.5"
            >
              <FaShareAlt className="w-3.5 h-3.5" />
              {copied ? 'Link Copied!' : 'Share'}
            </button>
            <button
              onClick={() => setReportModalOpen(true)}
              className="glass-btn px-3 py-2 text-xs font-bold text-amber-400 hover:text-red-400 flex items-center gap-1.5"
            >
              <FaFlag className="w-3.5 h-3.5" /> Report
            </button>
          </div>
        </div>

        {/* METRICS ROW */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 glass-pressed rounded-2xl text-xs font-semibold text-slate-300">
          <div>
            <span className="text-slate-400 font-normal block text-[11px]">File Size</span>
            <span className="font-bold text-white">{formatFileSize(doc.file_size)}</span>
          </div>
          <div>
            <span className="text-slate-400 font-normal block text-[11px]">Total Pages</span>
            <span className="font-bold text-white">{doc.page_count || 1} Pages</span>
          </div>
          <div>
            <span className="text-slate-400 font-normal block text-[11px]">Total Views</span>
            <span className="font-bold text-white">{doc.views_count || 0}</span>
          </div>
          <div>
            <span className="text-slate-400 font-normal block text-[11px]">Total Downloads</span>
            <span className="font-bold text-cyan-400">{doc.downloads_count || 0}</span>
          </div>
        </div>

        {/* DESCRIPTION */}
        {doc.description && (
          <div>
            <h4 className="font-bold text-white text-sm mb-1.5">Resource Description</h4>
            <p className="text-xs text-slate-300 leading-relaxed font-normal">{doc.description}</p>
          </div>
        )}

        {/* TAGS */}
        {doc.tags && (
          <div className="flex flex-wrap gap-1.5 pt-2">
            {doc.tags.split(',').map((tag, idx) => (
              <span key={idx} className="glass-badge px-2.5 py-1 text-xs text-slate-300">
                #{tag.trim()}
              </span>
            ))}
          </div>
        )}

        {/* ACTION BUTTONS */}
        <div className="pt-4 flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => onPreview(doc)}
            className="flex-1 glass-btn py-3.5 px-4 text-sm font-extrabold text-white hover:text-cyan-300 flex items-center justify-center gap-2"
          >
            <FaEye className="w-4 h-4 text-cyan-400" /> Read / Preview
          </button>
          <button
            onClick={() => onOpenSummary && onOpenSummary(doc)}
            className="flex-1 glass-btn py-3.5 px-4 text-sm font-extrabold text-white hover:text-amber-300 border-amber-500/30 hover:border-amber-400/60 bg-gradient-to-r from-amber-500/10 via-violet-500/10 to-indigo-500/10 flex items-center justify-center gap-2 shadow-lg hover:shadow-amber-500/20 transition-all duration-300"
          >
            <span className="text-amber-300 text-base">✨</span> Smart Summary
          </button>
          <button
            onClick={() => onDownload(doc)}
            className="flex-1 glass-btn-primary py-3.5 px-4 text-sm font-extrabold flex items-center justify-center gap-2"
          >
            <FaDownload className="w-4 h-4" /> Download PDF
          </button>
        </div>

      </div>

      {reportModalOpen && (
        <ReportModal
          doc={doc}
          onClose={() => setReportModalOpen(false)}
          onSuccess={() => alert('Report submitted successfully.')}
        />
      )}

    </div>
  );
}
