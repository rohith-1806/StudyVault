import React, { useState } from 'react';
import { 
  FaTimes, 
  FaSearchPlus, 
  FaSearchMinus, 
  FaDownload, 
  FaFilePdf, 
  FaExpand, 
  FaCompress, 
  FaSpinner, 
  FaExclamationTriangle,
  FaRedo
} from 'react-icons/fa';
import { api } from '../services/api';

export default function PdfViewerModal({ doc, onClose, onDownload, onViewRecorded, onOpenSummary }) {
  const [zoom, setZoom] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const hasRecordedRef = React.useRef(false);

  if (!doc) return null;

  const streamUrl = api.getStreamUrl(doc.id);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleRetry = () => {
    setIsLoading(true);
    setHasError(false);
  };

  const handleIframeLoad = async () => {
    setIsLoading(false);
    if (!hasRecordedRef.current && doc?.id) {
      hasRecordedRef.current = true;
      try {
        const res = await api.recordView(doc.id);
        if (res && res.views_count !== undefined && onViewRecorded) {
          onViewRecorded(doc.id, res.views_count);
        }
      } catch (err) {
        console.error('Failed to record document preview view:', err);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className={`glass-modal w-full flex flex-col overflow-hidden transition-all duration-300 shadow-2xl ${
        isFullscreen ? 'h-full max-w-full rounded-none' : 'max-w-5xl h-[88vh] rounded-2xl'
      }`}>
        
        {/* MODAL HEADER */}
        <div className="p-3 sm:px-5 border-b border-white/10 flex items-center justify-between glass-pressed rounded-t-2xl">
          <div className="flex items-center gap-2.5 min-w-0 pr-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 p-0.5 shadow-md shadow-violet-500/20 flex-shrink-0 flex items-center justify-center text-red-400">
              <FaFilePdf className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <h3 className="font-bold text-sm sm:text-[15px] truncate" title={doc.title}>
                {doc.title}
              </h3>
              <p className="text-[11px] text-slate-400 truncate">
                {doc.category_name || 'Resource'} • {doc.page_count || 1} Pages • {doc.uploader_name || 'Student'}
              </p>
            </div>
          </div>

          {/* TOOLBAR ACTIONS */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {/* ZOOM CONTROLS */}
            <div className="hidden sm:flex items-center glass-pressed p-1 rounded-xl gap-1">
              <button
                onClick={() => setZoom(prev => Math.max(50, prev - 25))}
                className="p-1 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition-colors"
                title="Zoom Out"
              >
                <FaSearchMinus className="w-3 h-3" />
              </button>
              <span className="text-[11px] font-mono font-bold px-1.5">{zoom}%</span>
              <button
                onClick={() => setZoom(prev => Math.min(200, prev + 25))}
                className="p-1 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition-colors"
                title="Zoom In"
              >
                <FaSearchPlus className="w-3 h-3" />
              </button>
            </div>

            {/* FULLSCREEN */}
            <button
              onClick={toggleFullscreen}
              className="p-2 glass-btn rounded-xl"
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? <FaCompress className="w-3.5 h-3.5" /> : <FaExpand className="w-3.5 h-3.5" />}
            </button>

            {/* SMART SUMMARY IN PREVIEW */}
            <button
              onClick={() => onOpenSummary && onOpenSummary(doc)}
              className="glass-btn px-3 py-1.5 text-xs font-bold text-amber-300 hover:text-amber-200 border-amber-500/30 hover:border-amber-400/60 bg-gradient-to-r from-amber-500/10 via-violet-500/10 to-indigo-500/10 flex items-center gap-1.5 rounded-xl shadow-md transition-all"
              title="Generate or view AI Smart Summary"
            >
              <span>✨</span>
              <span className="hidden sm:inline">Smart Summary</span>
            </button>

            {/* DOWNLOAD IN PREVIEW */}
            <button
              onClick={() => onDownload(doc)}
              className="glass-btn-primary px-3.5 py-1.5 text-xs font-semibold flex items-center gap-1.5 rounded-xl shadow-md"
              title="Download this PDF"
            >
              <FaDownload className="w-3 h-3 flex-shrink-0" />
              <span>Download</span>
            </button>

            {/* CLOSE PREVIEW */}
            <button
              onClick={onClose}
              className="p-2 glass-btn text-slate-400 hover:text-red-400 rounded-xl ml-1"
              title="Close Preview"
            >
              <FaTimes className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* PDF CANVAS / EMBED BODY */}
        <div className="flex-1 relative overflow-hidden flex items-center justify-center p-2 bg-slate-900/60">
          
          {/* LOADING SPINNER */}
          {isLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/40 backdrop-blur-sm z-10 space-y-3">
              <FaSpinner className="w-8 h-8 text-violet-400 animate-spin" />
              <p className="text-xs font-semibold text-slate-400">Loading PDF document...</p>
            </div>
          )}

          {/* ERROR FALLBACK */}
          {hasError ? (
            <div className="glass-card p-8 text-center max-w-md mx-auto space-y-4">
              <FaExclamationTriangle className="w-10 h-10 text-amber-400 mx-auto" />
              <h4 className="font-bold text-base">Unable to stream PDF</h4>
              <p className="text-xs text-slate-400">
                The document preview could not be loaded directly. You can try reloading or download the file directly.
              </p>
              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={handleRetry}
                  className="glass-btn px-4 py-2 text-xs font-semibold flex items-center gap-1.5"
                >
                  <FaRedo className="w-3 h-3" /> Retry
                </button>
                <button
                  onClick={() => onDownload(doc)}
                  className="glass-btn-primary px-4 py-2 text-xs font-semibold flex items-center gap-1.5"
                >
                  <FaDownload className="w-3 h-3" /> Download PDF
                </button>
              </div>
            </div>
          ) : (
            <div className="w-full h-full rounded-xl overflow-hidden shadow-inner pdf-viewer-canvas bg-white">
              <iframe
                key={`${doc.id}-${zoom}`}
                src={`${streamUrl}#zoom=${zoom}`}
                className="w-full h-full border-none bg-white"
                title={doc.title}
                onLoad={handleIframeLoad}
                onError={() => {
                  setIsLoading(false);
                  setHasError(true);
                }}
              />
            </div>
          )}

        </div>

        {/* MODAL FOOTER */}
        <div className="px-5 py-2.5 border-t border-white/10 glass-pressed rounded-b-2xl flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="glass-chip px-2.5 py-0.5 text-[10px] text-cyan-400 font-bold bg-cyan-500/10 border-cyan-500/30">
              Secure PDF Viewer
            </span>
            <span className="truncate max-w-[200px] sm:max-w-none">{doc.file_name}</span>
          </div>
          <span className="text-[11px] font-medium">{doc.page_count || 1} {doc.page_count === 1 ? 'Page' : 'Pages'}</span>
        </div>

      </div>
    </div>
  );
}
