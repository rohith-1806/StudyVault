import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { FaUserShield, FaEnvelope, FaLock, FaExclamationTriangle, FaSignInAlt } from 'react-icons/fa';

export default function AdminLogin({ navigate }) {
  const { adminLogin } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await adminLogin(email, password);
      navigate('/admin');
    } catch (err) {
      setError(err.message || 'Admin authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-16 px-4">
      <div className="glass-modal p-8 border border-pink-500/30">
        
        <div className="text-center space-y-2 mb-8">
          <div className="w-14 h-14 glass-btn mx-auto flex items-center justify-center text-pink-400 rounded-2xl mb-3">
            <FaUserShield className="w-7 h-7 stroke-[2.5]" />
          </div>
          <h2 className="text-2xl font-black text-white">Admin Portal Sign In</h2>
          <p className="text-xs text-slate-400 font-medium">StudyVault Document Moderation & Platform Control</p>
        </div>

        {error && (
          <div className="p-3.5 mb-6 glass-pressed bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-semibold rounded-xl flex items-center gap-2">
            <FaExclamationTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Admin Email</label>
            <div className="relative">
              <FaEnvelope className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@studyvault.edu"
                className="w-full glass-input pl-10 pr-4 py-3 text-xs font-semibold"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <FaLock className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full glass-input pl-10 pr-4 py-3 text-xs font-semibold"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full glass-btn-accent py-3.5 text-xs font-extrabold flex items-center justify-center gap-2"
          >
            <FaSignInAlt className="w-4 h-4" />
            {loading ? 'Authenticating Admin...' : 'Authenticate Admin'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-white/10 text-center">
          <button onClick={() => navigate('/login')} className="text-xs text-slate-400 font-bold hover:text-white">
            ← Back to Student Login
          </button>
        </div>

      </div>
    </div>
  );
}
