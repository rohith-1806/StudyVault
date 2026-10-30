import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { FaUser, FaEnvelope, FaLock, FaExclamationTriangle, FaMagic, FaCheckCircle } from 'react-icons/fa';

export default function Register({ navigate }) {
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const res = await register(fullName, email, password, confirmPassword);
      const msg = res?.message || 'Account created successfully. Please check your email for the welcome message.';
      setSuccessMessage(msg);
      setTimeout(() => {
        navigate('/library');
      }, 1600);
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12 px-4">
      <div className="glass-modal p-8 border border-white/20">
        
        {/* LOGO */}
        <div className="text-center space-y-2 mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 via-indigo-600 to-cyan-500 p-0.5 shadow-xl shadow-violet-500/20 mx-auto mb-3 flex items-center justify-center">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-violet-400">
              <FaMagic className="w-6 h-6 text-violet-400" />
            </div>
          </div>
          <h2 className="text-2xl font-black text-white">Create Student Account</h2>
          <p className="text-xs text-slate-400 font-medium">Join the student-to-student digital library</p>
        </div>

        {error && (
          <div className="p-3.5 mb-6 glass-pressed bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-semibold rounded-xl flex items-center gap-2">
            <FaExclamationTriangle className="w-4 h-4 flex-shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        {successMessage && (
          <div className="p-3.5 mb-6 glass-pressed bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold rounded-xl flex items-center gap-2 animate-fade-in">
            <FaCheckCircle className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Full Name *</label>
            <div className="relative">
              <FaUser className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Rahul Sharma"
                className="w-full glass-input pl-10 pr-4 py-3 text-xs font-semibold"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Email Address *</label>
            <div className="relative">
              <FaEnvelope className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
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
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Password (Min. 8 characters) *</label>
            <div className="relative">
              <FaLock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full glass-input pl-10 pr-4 py-3 text-xs font-semibold"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Confirm Password *</label>
            <div className="relative">
              <FaLock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full glass-input pl-10 pr-4 py-3 text-xs font-semibold"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full glass-btn-primary py-3.5 text-xs font-extrabold flex items-center justify-center gap-2"
            >
              <FaCheckCircle className="w-4 h-4 text-emerald-300" />
              {loading ? 'Creating Account...' : 'Register & Start Learning'}
            </button>
          </div>
        </form>

        <div className="mt-8 pt-6 border-t border-white/10 text-center">
          <p className="text-xs text-slate-400">
            Already have an account?{' '}
            <button onClick={() => navigate('/login')} className="text-violet-400 font-bold hover:underline">
              Sign In here
            </button>
          </p>
        </div>

      </div>
    </div>
  );
}
