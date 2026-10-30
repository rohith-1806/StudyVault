import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  FaUser, 
  FaEnvelope, 
  FaCalendarAlt, 
  FaCloudUploadAlt, 
  FaCheckCircle, 
  FaClock, 
  FaAward, 
  FaTrashAlt, 
  FaEye, 
  FaDownload, 
  FaFilePdf,
  FaExclamationTriangle,
  FaRedo
} from 'react-icons/fa';
import { api } from '../services/api';
import AccessTimer from '../components/AccessTimer';
import { formatFileSize } from '../components/DocumentCard';

export default function UserProfile({ navigate, onPreview }) {
  const { user, refreshUser } = useAuth();
  const [profileData, setProfileData] = useState(null);
  const [contributions, setContributions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  const fetchProfileAndDocs = async () => {
    setLoading(true);
    try {
      const [profRes, contribRes] = await Promise.all([
        api.getProfile(),
        api.getContributions()
      ]);
      setProfileData(profRes.profile);
      setContributions(contribRes.contributions || []);
    } catch (err) {
      console.error('Failed to load user profile:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileAndDocs();
  }, []);

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this contribution?')) return;
    setDeletingId(docId);
    try {
      await api.deleteDocument(docId);
      setContributions(prev => prev.filter(c => c.id !== docId));
      await refreshUser();
    } catch (err) {
      alert(err.message || 'Failed to delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  if (!user) {
    return (
      <div className="max-w-md mx-auto py-16 text-center glass-card p-8 space-y-4">
        <FaUser className="w-12 h-12 text-slate-500 mx-auto" />
        <h3 className="font-bold text-white text-lg">Please Sign In</h3>
        <button onClick={() => navigate('/login')} className="glass-btn-primary px-6 py-2.5 text-xs font-bold">
          Sign In
        </button>
      </div>
    );
  }

  const p = profileData || user;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-8 py-8 space-y-8">
      
      {/* USER PROFILE HEADER CARD */}
      <div className="glass-card p-6 sm:p-8 border border-white/20">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          
          <div className="flex items-center gap-4">
            <img
              src={p.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${p.id}`}
              alt={p.full_name}
              className="w-16 h-16 rounded-2xl glass-pressed p-1 bg-slate-900 border border-white/10"
            />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black text-white">{p.full_name}</h1>
                <span className="glass-badge px-2.5 py-0.5 text-[10px] text-violet-300 bg-violet-500/20 capitalize">
                  {p.role || 'Student'}
                </span>
              </div>
              <p className="text-xs text-slate-300 font-semibold mt-0.5 flex items-center gap-1.5">
                <FaEnvelope className="w-3 h-3 text-violet-400" /> {p.email}
              </p>
              <p className="text-[11px] text-slate-400 font-medium mt-1 flex items-center gap-1">
                <FaCalendarAlt className="w-3 h-3 text-slate-500" /> Member since {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Recently'}
              </p>
            </div>
          </div>

          {/* CONTRIBUTION BADGE & ACTION */}
          <div className="flex flex-col sm:items-end gap-2 w-full sm:w-auto">
            <div className="glass-chip px-4 py-2 text-xs font-extrabold text-violet-300 bg-violet-500/20 border-violet-500/30 flex items-center gap-2">
              <FaAward className="w-4 h-4 text-violet-400" />
              <span>{p.contribution_level || '🌱 New Contributor'}</span>
            </div>
            <button
              onClick={() => navigate('/upload')}
              className="glass-btn-primary px-5 py-2.5 text-xs font-bold flex items-center justify-center gap-1.5 w-full sm:w-auto"
            >
              <FaCloudUploadAlt className="w-4 h-4" /> Upload Document
            </button>
          </div>

        </div>
      </div>

      {/* 24-HOUR ACCESS COUNTDOWN TIMER */}
      <AccessTimer
        remainingSeconds={p.remaining_seconds || 0}
        onExpire={() => refreshUser()}
      />

      {/* STATS OVERVIEW */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-card p-5 text-center">
          <span className="text-2xl font-black text-violet-400">{p.total_uploads || contributions.length}</span>
          <span className="block text-xs font-bold text-slate-300 mt-1">Uploaded Docs</span>
        </div>
        <div className="glass-card p-5 text-center">
          <span className="text-2xl font-black text-emerald-400">{p.approved_uploads || 0}</span>
          <span className="block text-xs font-bold text-slate-300 mt-1">Approved Docs</span>
        </div>
        <div className="glass-card p-5 text-center">
          <span className="text-2xl font-black text-cyan-400">{p.total_views || 0}</span>
          <span className="block text-xs font-bold text-slate-300 mt-1">Total Views</span>
        </div>
        <div className="glass-card p-5 text-center">
          <span className="text-2xl font-black text-pink-400">{p.total_downloads || 0}</span>
          <span className="block text-xs font-bold text-slate-300 mt-1">Downloads Earned</span>
        </div>
      </div>

      {/* MY CONTRIBUTIONS TABLE / GRID */}
      <div className="glass-card p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-black text-white">My Contributions</h3>
            <p className="text-xs text-slate-400 font-medium">Manage your uploaded study resources</p>
          </div>
          <button
            onClick={fetchProfileAndDocs}
            className="glass-btn p-2 text-slate-300 hover:text-violet-400 rounded-xl"
            title="Refresh List"
          >
            <FaRedo className="w-3.5 h-3.5" />
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading contributions...</div>
        ) : contributions.length === 0 ? (
          <div className="glass-pressed p-12 text-center text-slate-400 rounded-2xl">
            <FaCloudUploadAlt className="w-12 h-12 text-slate-500 mx-auto mb-3" />
            <h4 className="font-bold text-white text-sm">You haven't uploaded any documents yet</h4>
            <p className="text-xs text-slate-400 mt-1">Upload a study document to earn 24 hours of unlimited library downloads.</p>
            <button onClick={() => navigate('/upload')} className="glass-btn-primary px-5 py-2 text-xs font-bold mt-4">
              Upload Your First Document
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-slate-400 font-bold uppercase tracking-wider">
                  <th className="py-3 px-3">Document Title</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-center">Views</th>
                  <th className="py-3 px-3 text-center">Downloads</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-semibold text-slate-200">
                {contributions.map(doc => (
                  <tr key={doc.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3.5 px-3">
                      <div className="flex items-center gap-2.5">
                        <FaFilePdf className="w-4 h-4 text-red-400 flex-shrink-0" />
                        <div>
                          <span className="font-bold text-white block truncate max-w-[200px]" title={doc.title}>
                            {doc.title}
                          </span>
                          <span className="text-[10px] text-slate-400 font-normal">
                            {formatFileSize(doc.file_size)} • {new Date(doc.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="glass-badge px-2.5 py-0.5 text-[10px] text-slate-300">
                        {doc.category_name || 'Resource'}
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      {doc.status === 'approved' && (
                        <span className="glass-chip px-2.5 py-0.5 text-[10px] text-emerald-300 bg-emerald-500/20 border-emerald-500/30 font-bold">
                          ✓ Approved
                        </span>
                      )}
                      {doc.status === 'pending_review' && (
                        <span className="glass-chip px-2.5 py-0.5 text-[10px] text-amber-300 bg-amber-500/20 border-amber-500/30 font-bold">
                          ⏳ Pending Review
                        </span>
                      )}
                      {doc.status === 'rejected' && (
                        <span className="glass-chip px-2.5 py-0.5 text-[10px] text-red-300 bg-red-500/20 border-red-500/30 font-bold" title={doc.rejection_reason}>
                          ✕ Rejected
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 text-center text-slate-400">{doc.views_count || 0}</td>
                    <td className="py-3.5 px-3 text-center text-cyan-400">{doc.downloads_count || 0}</td>
                    <td className="py-3.5 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => onPreview(doc)}
                          className="glass-btn p-1.5 text-slate-300 hover:text-cyan-400 rounded-lg"
                          title="Preview"
                        >
                          <FaEye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          disabled={deletingId === doc.id}
                          className="glass-btn p-1.5 text-slate-400 hover:text-red-400 rounded-lg"
                          title="Delete Contribution"
                        >
                          <FaTrashAlt className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>

    </div>
  );
}
