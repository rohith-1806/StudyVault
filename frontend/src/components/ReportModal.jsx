import React, { useState } from 'react';
import { FaFlag, FaTimes, FaExclamationTriangle, FaPaperPlane } from 'react-icons/fa';
import { api } from '../services/api';

const REPORT_REASONS = [
  { id: 'copyright_issue', label: 'Copyright Infringement / Pirated Content' },
  { id: 'wrong_content', label: 'Wrong or Misleading Content' },
  { id: 'spam', label: 'Spam or Advertising' },
  { id: 'malware_suspicious', label: 'Suspicious / Corrupted File' },
  { id: 'duplicate', label: 'Duplicate Document' },
  { id: 'inappropriate_content', label: 'Inappropriate / Offensive Content' },
  { id: 'other', label: 'Other Reason' }
];

export default function ReportModal({ doc, onClose, onSuccess }) {
  const [reason, setReason] = useState('copyright_issue');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!doc) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.reportDocument(doc.id, { reason, description });
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit report.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-modal w-full max-w-md p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 glass-btn p-2 text-slate-400 hover:text-red-400 rounded-xl"
        >
          <FaTimes className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 glass-pressed flex items-center justify-center text-amber-400 rounded-xl">
            <FaFlag className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-lg">Report Document</h3>
            <p className="text-xs text-slate-400 truncate max-w-[260px]">{doc.title}</p>
          </div>
        </div>

        {error && (
          <div className="p-3 mb-4 glass-pressed bg-red-500/20 border border-red-500/30 text-red-300 text-xs rounded-xl flex items-center gap-2">
            <FaExclamationTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              Reason for Reporting *
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full glass-input p-3 text-xs font-semibold bg-slate-900 text-white"
            >
              {REPORT_REASONS.map(r => (
                <option key={r.id} value={r.id} className="bg-slate-900 text-white">{r.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              Additional Details (Optional)
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide context or explanation..."
              className="w-full glass-input p-3 text-xs text-white placeholder-slate-500"
            />
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="glass-btn px-4 py-2 text-xs font-bold text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="glass-btn-primary px-5 py-2 text-xs font-bold flex items-center gap-1.5"
            >
              <FaPaperPlane className="w-3.5 h-3.5" />
              {submitting ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
