import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { FaBookOpen, FaSignInAlt, FaEnvelope, FaLock, FaExclamationTriangle, FaUserShield } from 'react-icons/fa';

export default function Login({ navigate }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/library');
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-16 px-4">
      <div className="glass-modal p-8 border border-white/20">
        
        {/* LOGO */}
        <div className="text-center space-y-2 mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 via-indigo-600 to-cyan-500 p-0.5 shadow-xl shadow-violet-500/20 mx-auto mb-3 flex items-center justify-center">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-violet-400">
              <FaBookOpen className="w-6 h-6 stroke-[2.5]" />
            </div>
          </div>
          <h2 className="text-2xl font-black text-white">Student Sign In</h2>
          <p className="text-xs text-slate-400 font-medium">Access your digital library account & contributions</p>
        </div>

        {error && (
          <div className="p-3.5 mb-6 glass-pressed bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-semibold rounded-xl flex items-center gap-2">
            <FaExclamationTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Email Address</label>
            <div className="relative">
              <FaEnvelope className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@university.edu"
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

          <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="rounded text-violet-600"
              />
              <span>Remember me</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full glass-btn-primary py-3.5 text-xs font-extrabold flex items-center justify-center gap-2"
          >
            <FaSignInAlt className="w-4 h-4" />
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-white/10 text-center space-y-3">
          <p className="text-xs text-slate-400">
            Don't have an account?{' '}
            <button onClick={() => navigate('/register')} className="text-violet-400 font-bold hover:underline">
              Register here
            </button>
          </p>
          <p className="text-[11px] text-slate-500">
            Are you an administrator?{' '}
            <button onClick={() => navigate('/admin/login')} className="text-pink-400 font-bold hover:underline inline-flex items-center gap-1">
              <FaUserShield className="w-3 h-3" /> Admin Login
            </button>
          </p>
        </div>

      </div>
    </div>
  );
}
