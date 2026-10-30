import React from 'react';
import { FaFilePdf, FaEye, FaDownload, FaUser, FaHdd } from 'react-icons/fa';

export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 KB';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export default function DocumentCard({ doc, onPreview, onDownload, onOpenSummary, navigate }) {
  const categoryName = doc.category_name || doc.category_id || 'Educational Resource';

  return (
    <div className="glass-card glass-card-hover p-4 sm:p-4 flex flex-col justify-between h-full group relative overflow-hidden transition-all duration-200">
      
      {/* GLOW DECORATIVE BACKDROP */}
      <div className="absolute top-0 right-0 w-28 h-28 bg-violet-600/10 rounded-full blur-2xl group-hover:bg-violet-600/20 transition-all pointer-events-none" />

      {/* CARD CONTENT */}
      <div>
        {/* HEADER: CATEGORY CHIP & FILE METRICS */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <span 
            className="glass-chip px-2.5 py-0.5 text-[10px] font-bold text-violet-400 bg-violet-500/10 border-violet-500/30 truncate max-w-[140px]"
            title={categoryName}
          >
            {categoryName}
          </span>
          <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1 flex-shrink-0">
            <FaHdd className="w-3 h-3 text-slate-400" />
            {formatFileSize(doc.file_size)} • {doc.page_count || 1} {doc.page_count === 1 ? 'Page' : 'Pages'}
          </span>
        </div>

        {/* THUMBNAIL & TITLE (2-LINE CLAMP WITH TOOLTIP) */}
        <div className="flex items-start gap-2.5 mb-2">
          <div 
            onClick={() => navigate ? navigate(`/document/${doc.id}`) : onPreview(doc)}
            className="w-10 h-11 rounded-xl bg-gradient-to-br from-violet-600 via-indigo-600 to-cyan-500 p-0.5 shadow-md shadow-violet-500/20 flex-shrink-0 group-hover:scale-105 transition-transform flex items-center justify-center cursor-pointer"
          >
            <div className="w-full h-full bg-slate-950/90 rounded-[10px] flex items-center justify-center text-red-400">
              <FaFilePdf className="w-5 h-5" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h3 
              onClick={() => navigate ? navigate(`/document/${doc.id}`) : onPreview(doc)}
              className="font-semibold text-sm sm:text-[15px] leading-snug line-clamp-2 group-hover:text-violet-400 transition-colors cursor-pointer"
              title={doc.title}
            >
              {doc.title}
            </h3>
            {doc.subject && (
              <p className="text-[11px] font-medium text-slate-400 truncate mt-0.5" title={doc.subject}>
                Subject: <span className="text-slate-300 font-semibold">{doc.subject}</span>
              </p>
            )}
            {doc.course && (
              <p className="text-[11px] text-slate-400 truncate" title={doc.course}>
                Course: {doc.course} {doc.semester ? `(${doc.semester})` : ''}
              </p>
            )}
          </div>
        </div>

        {/* DESCRIPTION (2 LINES) */}
        {doc.description && (
          <p className="text-[12px] text-slate-400 line-clamp-2 mb-2 leading-relaxed font-normal" title={doc.description}>
            {doc.description}
          </p>
        )}

        {/* TAGS */}
        {doc.tags && (
          <div className="flex flex-wrap gap-1 mb-2">
            {doc.tags.split(',').slice(0, 3).map((tag, idx) => (
              <span key={idx} className="glass-badge px-2 py-0.5 text-[10px] text-slate-400 font-medium">
                #{tag.trim()}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* FOOTER METRICS & ACTIONS */}
      <div className="pt-2.5 border-t border-white/10 mt-auto">
        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2.5">
          <div className="flex items-center gap-1 font-medium truncate max-w-[130px]" title={doc.uploader_name || 'Student'}>
            <FaUser className="w-3 h-3 text-slate-400" />
            <span className="truncate">{doc.uploader_name || 'Student'}</span>
          </div>
          <div className="flex items-center gap-2.5 font-bold">
            <span className="flex items-center gap-1" title="Views">
              <FaEye className="w-3.5 h-3.5 text-slate-400" />
              {doc.views_count || 0}
            </span>
            <span className="flex items-center gap-1 text-cyan-400" title="Downloads">
              <FaDownload className="w-3 h-3" />
              {doc.downloads_count || 0}
            </span>
          </div>
        </div>

        {/* BUTTONS (PREVENT OVERFLOW) */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => onPreview(doc)}
            className="glass-btn py-1.5 px-3 text-xs font-semibold flex items-center justify-center gap-1.5 rounded-xl transition-all"
            title="Preview PDF"
          >
            <FaEye className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" /> 
            <span>Preview</span>
          </button>
          <button
            onClick={() => onDownload(doc)}
            className="glass-btn-primary py-1.5 px-3 text-xs font-semibold flex items-center justify-center gap-1.5 rounded-xl transition-all"
            title="Download PDF"
          >
            <FaDownload className="w-3.5 h-3.5 flex-shrink-0" /> 
            <span>Download</span>
          </button>
        </div>
      </div>

    </div>
  );
}
