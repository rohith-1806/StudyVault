import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  FaUserShield, 
  FaUsers, 
  FaFilePdf, 
  FaCheckCircle, 
  FaTimesCircle, 
  FaClock, 
  FaEye, 
  FaDownload, 
  FaTrashAlt, 
  FaFlag, 
  FaUserTimes, 
  FaUserCheck, 
  FaRedo
} from 'react-icons/fa';
import { api } from '../services/api';
import { formatFileSize } from '../components/DocumentCard';

export default function AdminDashboard({ navigate, onPreview }) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('moderation');
  const [stats, setStats] = useState(null);
  const [pendingDocs, setPendingDocs] = useState([]);
  const [usersList, setUsersList] = useState([]);
  const [reportsList, setReportsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, pendingRes, usersRes, reportsRes] = await Promise.all([
        api.getAdminDashboard(),
        api.getPendingDocuments(),
        api.getAdminUsers(),
        api.getAdminReports()
      ]);
      setStats(dashRes.stats);
      setPendingDocs(pendingRes.documents || []);
      setUsersList(usersRes.users || []);
      setReportsList(reportsRes.reports || []);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchData();
    }
  }, [user]);

  if (!user || user.role !== 'admin') {
    return (
      <div className="max-w-md mx-auto py-16 text-center glass-card p-8 space-y-4">
        <FaUserShield className="w-12 h-12 text-pink-400 mx-auto" />
        <h3 className="font-bold text-white text-lg">Admin Access Required</h3>
        <p className="text-xs text-slate-400">You must be logged in as an administrator to access the admin portal.</p>
        <button onClick={() => navigate('/admin/login')} className="glass-btn-accent px-6 py-2.5 text-xs font-bold">
          Admin Sign In
        </button>
      </div>
    );
  }

  const handleApprove = async (docId) => {
    try {
      const res = await api.approveDocument(docId);
      setActionMessage(res.message || 'Document approved.');
      setPendingDocs(prev => prev.filter(d => d.id !== docId));
      fetchData();
    } catch (err) {
      alert(err.message || 'Approval failed.');
    }
  };

  const handleReject = async (docId) => {
    const reason = prompt('Enter rejection reason (e.g. Copyright issue, Low quality):');
    if (reason === null) return;
    try {
      const res = await api.rejectDocument(docId, { reason });
      setActionMessage('Document rejected.');
      setPendingDocs(prev => prev.filter(d => d.id !== docId));
      fetchData();
    } catch (err) {
      alert(err.message || 'Rejection failed.');
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!window.confirm('Permanently delete this document from library?')) return;
    try {
      await api.deleteDocumentAdmin(docId);
      setPendingDocs(prev => prev.filter(d => d.id !== docId));
      fetchData();
    } catch (err) {
      alert(err.message || 'Delete failed.');
    }
  };

  const handleToggleUser = async (userId, currentActive) => {
    try {
      await api.toggleUserStatus(userId, !currentActive);
      setUsersList(prev => prev.map(u => u.id === userId ? { ...u, is_active: currentActive ? 0 : 1 } : u));
    } catch (err) {
      alert(err.message || 'Failed to update user status.');
    }
  };

  const handleResolveReport = async (reportId) => {
    try {
      await api.resolveReport(reportId, 'resolved');
      setReportsList(prev => prev.filter(r => r.id !== reportId));
    } catch (err) {
      alert(err.message || 'Failed to resolve report.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-8">
      
      {/* ADMIN HEADER */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FaUserShield className="w-7 h-7 text-pink-400" />
            <h1 className="text-3xl font-black text-white">Admin Control Center</h1>
          </div>
          <p className="text-xs text-slate-400 font-medium mt-0.5">StudyVault System Moderation & Analytics</p>
        </div>
        <button
          onClick={fetchData}
          className="glass-btn px-4 py-2 text-xs font-bold text-slate-200 hover:text-white flex items-center gap-1.5"
        >
          <FaRedo className="w-3.5 h-3.5 text-pink-400" /> Refresh Analytics
        </button>
      </div>

      {actionMessage && (
        <div className="p-4 glass-pressed bg-emerald-500/20 text-emerald-300 text-xs font-bold rounded-2xl flex items-center justify-between border border-emerald-500/30">
          <span>✓ {actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* DASHBOARD STATS OVERVIEW CARDS */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-white">{stats.total_users}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Total Users</span>
          </div>
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-violet-400">{stats.total_documents}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Total Docs</span>
          </div>
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-emerald-400">{stats.approved_documents}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Approved</span>
          </div>
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-amber-400">{stats.pending_documents}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Pending</span>
          </div>
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-red-400">{stats.rejected_documents}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Rejected</span>
          </div>
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-cyan-400">{stats.total_downloads}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Downloads</span>
          </div>
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-slate-300">{stats.total_views}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Views</span>
          </div>
          <div className="glass-card p-3.5 text-center">
            <span className="text-xl font-black text-emerald-400">{stats.active_contributors}</span>
            <span className="block text-[10px] font-bold text-slate-400 mt-0.5">Contributors</span>
          </div>
        </div>
      )}

      {/* ADMIN TABS NAVIGATION */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2">
        <button
          onClick={() => setActiveTab('moderation')}
          className={`glass-chip px-5 py-2.5 text-xs font-bold flex items-center gap-2 ${
            activeTab === 'moderation' ? 'glass-chip-active' : 'text-slate-300'
          }`}
        >
          <FaClock className="w-3.5 h-3.5" /> Pending Moderation ({pendingDocs.length})
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`glass-chip px-5 py-2.5 text-xs font-bold flex items-center gap-2 ${
            activeTab === 'users' ? 'glass-chip-active' : 'text-slate-300'
          }`}
        >
          <FaUsers className="w-3.5 h-3.5" /> User Management ({usersList.length})
        </button>
        <button
          onClick={() => setActiveTab('reports')}
          className={`glass-chip px-5 py-2.5 text-xs font-bold flex items-center gap-2 ${
            activeTab === 'reports' ? 'glass-chip-active' : 'text-slate-300'
          }`}
        >
          <FaFlag className="w-3.5 h-3.5" /> Document Reports ({reportsList.length})
        </button>
      </div>

      {/* TAB 1: PENDING MODERATION QUEUE */}
      {activeTab === 'moderation' && (
        <div className="glass-card p-6 sm:p-8 space-y-6">
          <h3 className="text-lg font-black text-white">Pending Review Queue</h3>
          {pendingDocs.length === 0 ? (
            <div className="glass-pressed p-12 text-center text-slate-400 rounded-2xl">
              <FaCheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-2" />
              <p className="font-bold text-sm">Moderation queue is empty!</p>
              <p className="text-xs text-slate-500 mt-1">All uploaded documents are verified.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingDocs.map(doc => (
                <div key={doc.id} className="glass-pressed p-5 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div className="flex items-start gap-3.5 min-w-0">
                    <FaFilePdf className="w-7 h-7 text-red-400 flex-shrink-0 mt-1" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm truncate">{doc.title}</span>
                        <span className="glass-badge px-2 py-0.5 text-[10px] text-violet-300">{doc.category_name}</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">
                        Uploader: <strong className="text-slate-200">{doc.uploader_name}</strong> • Size: {formatFileSize(doc.file_size)} • Pages: {doc.page_count}
                      </p>
                      {doc.description && <p className="text-xs text-slate-300 mt-1 line-clamp-1">{doc.description}</p>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0 self-end md:self-auto">
                    <button
                      onClick={() => onPreview(doc)}
                      className="glass-btn px-3 py-1.5 text-xs font-bold text-slate-200 hover:text-cyan-400 flex items-center gap-1"
                    >
                      <FaEye className="w-3.5 h-3.5" /> Preview
                    </button>
                    <button
                      onClick={() => handleApprove(doc.id)}
                      className="glass-btn-primary px-4 py-1.5 text-xs font-bold flex items-center gap-1"
                    >
                      <FaCheckCircle className="w-3.5 h-3.5" /> Approve & Grant 24h
                    </button>
                    <button
                      onClick={() => handleReject(doc.id)}
                      className="glass-btn px-3 py-1.5 text-xs font-bold text-red-400 hover:bg-red-500/20"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => handleDeleteDoc(doc.id)}
                      className="glass-btn p-1.5 text-slate-400 hover:text-red-400 rounded-lg"
                      title="Delete"
                    >
                      <FaTrashAlt className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: USER MANAGEMENT */}
      {activeTab === 'users' && (
        <div className="glass-card p-6 sm:p-8 space-y-6">
          <h3 className="text-lg font-black text-white">Registered Student Accounts</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-slate-400 font-bold uppercase">
                  <th className="py-3 px-3">Student Name</th>
                  <th className="py-3 px-3">Email</th>
                  <th className="py-3 px-3">Role</th>
                  <th className="py-3 px-3">Account Status</th>
                  <th className="py-3 px-3">Joined Date</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-semibold text-slate-200">
                {usersList.map(u => (
                  <tr key={u.id}>
                    <td className="py-3 px-3 font-bold text-white">{u.full_name}</td>
                    <td className="py-3 px-3 text-slate-300">{u.email}</td>
                    <td className="py-3 px-3">
                      <span className={`glass-badge px-2 py-0.5 text-[10px] ${u.role === 'admin' ? 'text-pink-300 bg-pink-500/20' : 'text-slate-300'}`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {u.is_active ? (
                        <span className="glass-chip px-2.5 py-0.5 text-[10px] text-emerald-300 bg-emerald-500/20 border-emerald-500/30 font-bold">
                          Active
                        </span>
                      ) : (
                        <span className="glass-chip px-2.5 py-0.5 text-[10px] text-red-300 bg-red-500/20 border-red-500/30 font-bold">
                          Disabled
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-normal">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-right">
                      {u.role !== 'admin' && (
                        <button
                          onClick={() => handleToggleUser(u.id, Boolean(u.is_active))}
                          className={`glass-btn px-3 py-1 text-xs font-bold ${
                            u.is_active ? 'text-red-400 hover:bg-red-500/20' : 'text-emerald-400 hover:bg-emerald-500/20'
                          }`}
                        >
                          {u.is_active ? 'Disable Account' : 'Enable Account'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: DOCUMENT REPORTS */}
      {activeTab === 'reports' && (
        <div className="glass-card p-6 sm:p-8 space-y-6">
          <h3 className="text-lg font-black text-white">Document Infringement Reports</h3>
          {reportsList.length === 0 ? (
            <div className="glass-pressed p-12 text-center text-slate-400 rounded-2xl">
              <FaCheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-2" />
              <p className="font-bold text-sm">No open reports!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {reportsList.map(r => (
                <div key={r.id} className="glass-pressed p-4 rounded-2xl flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <span className="glass-chip px-2.5 py-0.5 text-[10px] font-bold text-red-300 bg-red-500/20 border-red-500/30 uppercase">
                      {r.reason?.replace('_', ' ')}
                    </span>
                    <h4 className="font-bold text-white text-sm mt-1">{r.document_title || 'Document'}</h4>
                    <p className="text-xs text-slate-400">Reported by: {r.reporter_name} ({r.reporter_email})</p>
                    {r.description && <p className="text-xs text-slate-300 font-normal">{r.description}</p>}
                  </div>
                  <button
                    onClick={() => handleResolveReport(r.id)}
                    className="glass-btn px-4 py-1.5 text-xs font-bold text-cyan-400"
                  >
                    Mark Resolved
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
}
