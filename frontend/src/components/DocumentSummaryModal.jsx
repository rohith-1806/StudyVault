import React, { useState, useEffect } from 'react';
import { 
  FaTimes, 
  FaSpinner, 
  FaExclamationTriangle, 
  FaRedo, 
  FaCopy, 
  FaCheck, 
  FaBookOpen, 
  FaGraduationCap, 
  FaLightbulb, 
  FaListUl, 
  FaStar, 
  FaDownload, 
  FaLock, 
  FaCloudUploadAlt,
  FaFilePdf
} from 'react-icons/fa';
import { api, getToken } from '../services/api';

export default function DocumentSummaryModal({ doc, onClose, onDownload, navigate }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [loadingStep, setLoadingStep] = useState(1);

  useEffect(() => {
    if (!doc?.id) return;
    loadSummary(false);
  }, [doc?.id]);

  // Loading animation step progression
  useEffect(() => {
    if (!loading) return;
    const interval = setInterval(() => {
      setLoadingStep(prev => (prev < 3 ? prev + 1 : 1));
    }, 1800);
    return () => clearInterval(interval);
  }, [loading]);

  const loadSummary = async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    setLoadingStep(1);

    const token = getToken();
    if (!token) {
      setLoading(false);
      setError({
        code: 'AUTH_REQUIRED',
        message: 'Please log in to generate or view AI Smart Summaries.'
      });
      return;
    }

    try {
      const res = await api.summarizeDocument(doc.id, forceRefresh);
      if (res && res.summary) {
        setSummaryData(res);
      } else {
        throw new Error('Summary data could not be retrieved.');
      }
    } catch (err) {
      console.error('Failed to summarize document:', err);
      setError({
        code: err.code || 'UNKNOWN_ERROR',
        status: err.status,
        message: err.message || 'Failed to generate smart summary.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!summaryData?.summary) return;
    const s = summaryData.summary;
    let textToCopy = s.raw_markdown || '';

    if (!textToCopy) {
      textToCopy = `# Smart Summary: ${summaryData.title || doc.title}\n\n` +
        `## Overview\n${s.overview}\n\n` +
        `## Key Points\n${(s.key_points || []).map(p => `- ${p}`).join('\n')}\n\n` +
        `## Important Definitions\n${(s.important_definitions || []).map(d => `- **${d.term || 'Term'}**: ${d.definition || ''}`).join('\n')}\n\n` +
        `## Exam Revision Notes\n${(s.exam_revision_notes || []).map(n => `- ${n}`).join('\n')}\n\n` +
        `## Conclusion\n${s.conclusion}`;
    }

    navigator.clipboard.writeText(textToCopy).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    }).catch(err => {
      console.error('Copy failed:', err);
    });
  };

  if (!doc) return null;

  const s = summaryData?.summary;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-950/80 backdrop-blur-md animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        className="glass-modal w-full max-w-4xl max-h-[92vh] flex flex-col rounded-3xl border border-white/20 shadow-2xl overflow-hidden relative"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* HEADER BAR */}
        <div className="p-4 sm:p-6 border-b border-white/10 flex items-center justify-between gap-3 bg-gradient-to-r from-violet-600/10 via-indigo-600/10 to-transparent">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-400 to-violet-600 p-0.5 shadow-lg flex-shrink-0 flex items-center justify-center">
              <div className="w-full h-full bg-slate-900 rounded-[14px] flex items-center justify-center text-amber-300 font-bold text-lg">
                ✨
              </div>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-extrabold text-base sm:text-lg text-white truncate">
                  AI Smart Summary
                </h3>
                {summaryData?.cached && (
                  <span className="glass-chip px-2 py-0.5 text-[10px] font-bold text-emerald-400 border-emerald-500/30 bg-emerald-500/10 rounded-full">
                    ⚡ Instant (Cached)
                  </span>
                )}
                {summaryData?.model && (
                  <span className="glass-chip hidden sm:inline-block px-2 py-0.5 text-[10px] font-mono text-violet-300 rounded-full">
                    {summaryData.model}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 truncate max-w-md">
                {doc.title || 'Academic Resource'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {summaryData && !loading && (
              <>
                <button
                  onClick={handleCopy}
                  className="glass-btn px-3 py-1.5 text-xs font-semibold text-slate-300 hover:text-white flex items-center gap-1.5 rounded-xl transition-all"
                  title="Copy full summary to clipboard"
                >
                  {copied ? <FaCheck className="w-3 h-3 text-emerald-400" /> : <FaCopy className="w-3 h-3 text-cyan-400" />}
                  <span className="hidden sm:inline">{copied ? 'Copied!' : 'Copy'}</span>
                </button>
                <button
                  onClick={() => loadSummary(true)}
                  className="glass-btn p-2 text-slate-400 hover:text-amber-300 rounded-xl transition-all"
                  title="Regenerate summary"
                >
                  <FaRedo className="w-3.5 h-3.5" />
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="glass-btn p-2 text-slate-400 hover:text-red-400 rounded-xl transition-all"
              title="Close Summary"
            >
              <FaTimes className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* SECTION TABS (Only shown when summary is loaded) */}
        {!loading && !error && s && (
          <div className="flex items-center gap-1.5 px-4 sm:px-6 pt-3 pb-2 border-b border-white/5 overflow-x-auto scrollbar-none bg-slate-900/30">
            {[
              { id: 'all', label: 'All Sections', icon: FaBookOpen },
              { id: 'overview', label: 'Overview', icon: FaBookOpen },
              { id: 'key_points', label: 'Key Points', icon: FaListUl },
              { id: 'definitions', label: 'Definitions', icon: FaLightbulb },
              { id: 'exam_notes', label: 'Exam Notes', icon: FaStar },
              { id: 'conclusion', label: 'Conclusion', icon: FaGraduationCap }
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 whitespace-nowrap transition-all ${
                    isActive 
                      ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md' 
                      : 'glass-btn text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon className="w-3 h-3" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* MODAL BODY */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">

          {/* LOADING STATE */}
          {loading && (
            <div className="py-16 px-4 flex flex-col items-center justify-center text-center space-y-6">
              <div className="relative">
                <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-amber-400 via-violet-600 to-cyan-400 animate-spin p-0.5 shadow-2xl flex items-center justify-center">
                  <div className="w-full h-full bg-slate-950 rounded-[22px] flex items-center justify-center">
                    <FaBookOpen className="w-6 h-6 text-amber-300 animate-pulse" />
                  </div>
                </div>
              </div>
              <div className="space-y-2 max-w-sm">
                <h4 className="text-base font-extrabold text-white">
                  Generating AI Smart Summary
                </h4>
                <p className="text-xs text-slate-400">
                  {loadingStep === 1 && "Reading and extracting text from stored PDF..."}
                  {loadingStep === 2 && "Analyzing key topics, concepts, and definitions..."}
                  {loadingStep === 3 && "Synthesizing exam revision notes and study takeaways..."}
                </p>
              </div>

              {/* Shimmer skeleton */}
              <div className="w-full max-w-lg space-y-3 pt-4">
                <div className="h-4 bg-white/10 rounded-lg animate-pulse w-3/4 mx-auto"></div>
                <div className="h-3 bg-white/5 rounded-lg animate-pulse w-5/6 mx-auto"></div>
                <div className="h-3 bg-white/5 rounded-lg animate-pulse w-2/3 mx-auto"></div>
              </div>
            </div>
          )}

          {/* ERROR STATE */}
          {!loading && error && (
            <div className="py-10 px-4 max-w-lg mx-auto text-center space-y-5">
              <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
                {error.code === 'ACCESS_DENIED' || error.code === 'AUTH_REQUIRED' ? (
                  <FaLock className="w-6 h-6" />
                ) : (
                  <FaExclamationTriangle className="w-6 h-6" />
                )}
              </div>

              <div className="space-y-2">
                <h4 className="text-base font-extrabold text-white">
                  {error.code === 'SCANNED_PDF_NO_TEXT'
                    ? 'Scanned PDF (No Digital Text)'
                    : error.code === 'ACCESS_DENIED'
                    ? '24-Hour Access Required'
                    : error.code === 'AUTH_REQUIRED'
                    ? 'Authentication Required'
                    : 'Summarization Unavailable'}
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {error.message}
                </p>
              </div>

              {/* Contextual Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center pt-3">
                {error.code === 'SCANNED_PDF_NO_TEXT' && onDownload && (
                  <button
                    onClick={() => {
                      onClose();
                      onDownload(doc);
                    }}
                    className="glass-btn-primary px-5 py-2.5 text-xs font-bold flex items-center justify-center gap-2 rounded-xl"
                  >
                    <FaDownload className="w-3 h-3" /> Download Resource Instead
                  </button>
                )}

                {error.code === 'ACCESS_DENIED' && navigate && (
                  <button
                    onClick={() => {
                      onClose();
                      navigate('/upload');
                    }}
                    className="glass-btn-primary px-5 py-2.5 text-xs font-bold flex items-center justify-center gap-2 rounded-xl"
                  >
                    <FaCloudUploadAlt className="w-3.5 h-3.5" /> Upload Document to Unlock
                  </button>
                )}

                {error.code === 'AUTH_REQUIRED' && navigate && (
                  <button
                    onClick={() => {
                      onClose();
                      navigate('/login');
                    }}
                    className="glass-btn-primary px-5 py-2.5 text-xs font-bold flex items-center justify-center gap-2 rounded-xl"
                  >
                    Go to Login
                  </button>
                )}

                {error.code !== 'ACCESS_DENIED' && error.code !== 'AUTH_REQUIRED' && error.code !== 'SCANNED_PDF_NO_TEXT' && (
                  <button
                    onClick={() => loadSummary(true)}
                    className="glass-btn px-5 py-2.5 text-xs font-bold flex items-center justify-center gap-2 rounded-xl text-slate-300 hover:text-white"
                  >
                    <FaRedo className="w-3 h-3" /> Retry Summarization
                  </button>
                )}
              </div>
            </div>
          )}

          {/* LOADED SUMMARY CONTENT */}
          {!loading && !error && s && (
            <div className="space-y-6">

              {/* 1. OVERVIEW */}
              {(activeTab === 'all' || activeTab === 'overview') && (
                <div className="glass-card p-5 sm:p-6 rounded-2xl border border-white/10 space-y-3 relative overflow-hidden">
                  <div className="flex items-center gap-2.5 text-cyan-400">
                    <FaBookOpen className="w-4 h-4 flex-shrink-0" />
                    <h4 className="text-sm font-extrabold text-white tracking-wide uppercase">
                      Overview
                    </h4>
                  </div>
                  <div className="text-xs sm:text-sm text-slate-200 leading-relaxed font-normal whitespace-pre-line space-y-2">
                    {s.overview}
                  </div>
                </div>
              )}

              {/* 2. KEY POINTS */}
              {(activeTab === 'all' || activeTab === 'key_points') && (
                <div className="glass-card p-5 sm:p-6 rounded-2xl border border-white/10 space-y-4">
                  <div className="flex items-center gap-2.5 text-violet-400">
                    <FaListUl className="w-4 h-4 flex-shrink-0" />
                    <h4 className="text-sm font-extrabold text-white tracking-wide uppercase">
                      Key Points
                    </h4>
                  </div>
                  <ul className="space-y-2.5">
                    {(s.key_points || []).map((point, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-xs sm:text-sm text-slate-200">
                        <span className="w-5 h-5 rounded-lg bg-violet-500/10 border border-violet-500/30 text-violet-300 flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="leading-relaxed">{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 3. IMPORTANT DEFINITIONS */}
              {(activeTab === 'all' || activeTab === 'definitions') && (
                <div className="glass-card p-5 sm:p-6 rounded-2xl border border-white/10 space-y-4">
                  <div className="flex items-center gap-2.5 text-amber-400">
                    <FaLightbulb className="w-4 h-4 flex-shrink-0" />
                    <h4 className="text-sm font-extrabold text-white tracking-wide uppercase">
                      Important Definitions
                    </h4>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {(s.important_definitions || []).map((def, idx) => (
                      <div key={idx} className="glass-pressed p-3.5 rounded-xl border border-white/5 space-y-1.5">
                        <span className="inline-block px-2 py-0.5 text-[11px] font-extrabold text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                          {def.term || `Concept ${idx + 1}`}
                        </span>
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {def.definition || ''}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 4. EXAM REVISION NOTES */}
              {(activeTab === 'all' || activeTab === 'exam_notes') && (
                <div className="glass-card p-5 sm:p-6 rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-500/5 via-transparent to-violet-500/5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5 text-amber-300">
                      <FaStar className="w-4 h-4 flex-shrink-0" />
                      <h4 className="text-sm font-extrabold text-white tracking-wide uppercase">
                        Exam Revision Notes
                      </h4>
                    </div>
                    <span className="glass-badge px-2.5 py-0.5 text-[10px] font-extrabold text-amber-300">
                      High Yield
                    </span>
                  </div>
                  <div className="space-y-2.5">
                    {(s.exam_revision_notes || []).map((note, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10 text-xs sm:text-sm text-slate-200">
                        <span className="text-amber-400 font-bold text-xs mt-0.5">📌</span>
                        <span className="leading-relaxed">{note}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 5. CONCLUSION */}
              {(activeTab === 'all' || activeTab === 'conclusion') && (
                <div className="glass-card p-5 sm:p-6 rounded-2xl border border-white/10 space-y-3">
                  <div className="flex items-center gap-2.5 text-emerald-400">
                    <FaGraduationCap className="w-4 h-4 flex-shrink-0" />
                    <h4 className="text-sm font-extrabold text-white tracking-wide uppercase">
                      Conclusion
                    </h4>
                  </div>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {s.conclusion}
                  </p>
                </div>
              )}

            </div>
          )}

        </div>

        {/* FOOTER BAR */}
        <div className="p-4 sm:p-5 border-t border-white/10 bg-slate-900/40 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {summaryData?.page_count && (
              <span>{summaryData.page_count} {summaryData.page_count === 1 ? 'page' : 'pages'}</span>
            )}
            {summaryData?.char_count && (
              <span>• {summaryData.char_count.toLocaleString()} chars</span>
            )}
            {summaryData?.chunks_processed && summaryData.chunks_processed > 1 && (
              <span>• {summaryData.chunks_processed} chunks analyzed</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {onDownload && (
              <button
                onClick={() => onDownload(doc)}
                className="glass-btn px-4 py-2 text-xs font-bold text-slate-200 hover:text-white flex items-center gap-1.5 rounded-xl transition-all"
              >
                <FaDownload className="w-3 h-3 text-cyan-400" /> Download PDF
              </button>
            )}
            <button
              onClick={onClose}
              className="glass-btn-primary px-5 py-2 text-xs font-bold rounded-xl"
            >
              Done
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
