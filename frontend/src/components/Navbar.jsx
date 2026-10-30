import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { 
  FaBookOpen, 
  FaCloudUploadAlt, 
  FaBook, 
  FaUser, 
  FaSignOutAlt, 
  FaUserShield, 
  FaClock, 
  FaBars, 
  FaTimes,
  FaMagic,
  FaSun,
  FaMoon
} from 'react-icons/fa';

export default function Navbar({ currentPath, navigate }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const formatRemainingTime = (seconds) => {
    if (!seconds || seconds <= 0) return null;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${mins}m`;
  };

  const remainingStr = user ? formatRemainingTime(user.remaining_seconds) : null;
  const isAccessActive = user?.access_active || user?.role === 'admin';

  return (
    <header className="sticky top-0 z-40 px-3 sm:px-6 py-2">
      {/* FLOATING GLASS BAR */}
      <div className="max-w-7xl mx-auto glass-card py-2 px-3 sm:px-5 flex items-center justify-between shadow-xl">
        
        {/* LOGO */}
        <div 
          onClick={() => navigate('/')} 
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 via-indigo-600 to-cyan-500 p-0.5 shadow-md shadow-violet-500/20 group-hover:scale-105 transition-transform flex items-center justify-center">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center text-violet-400">
              <FaBookOpen className="w-3.5 h-3.5" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1">
              <span className="font-extrabold text-lg sm:text-xl tracking-tight">Study</span>
              <span className="font-extrabold text-lg sm:text-xl tracking-tight bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">Vault</span>
            </div>
            <p className="text-[8.5px] font-bold text-slate-400 tracking-wider uppercase">Student Digital Library</p>
          </div>
        </div>

        {/* DESKTOP NAV LINKS */}
        <nav className="hidden md:flex items-center gap-1.5">
          <button
            onClick={() => navigate('/library')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 ${
              currentPath === '/library' ? 'glass-chip-active' : 'glass-btn hover:text-violet-400'
            }`}
          >
            <FaBook className="w-3.5 h-3.5 text-cyan-400" />
            <span>Digital Library</span>
          </button>

          <button
            onClick={() => navigate('/upload')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 ${
              currentPath === '/upload' ? 'glass-chip-active' : 'glass-btn hover:text-violet-400'
            }`}
          >
            <FaCloudUploadAlt className="w-3.5 h-3.5 text-violet-400" />
            <span>Upload PDF</span>
          </button>

          {user?.role === 'admin' && (
            <button
              onClick={() => navigate('/admin')}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 ${
                currentPath.startsWith('/admin') ? 'glass-chip-active' : 'glass-btn text-pink-400 hover:text-pink-300'
              }`}
            >
              <FaUserShield className="w-3.5 h-3.5 text-pink-400" />
              <span>Admin Portal</span>
            </button>
          )}
        </nav>

        {/* USER ACCESS BADGE, THEME TOGGLE & AUTH ACTIONS */}
        <div className="hidden md:flex items-center gap-2">
          {/* THEME TOGGLE BUTTON */}
          <button
            onClick={toggleTheme}
            className="p-2 glass-btn rounded-xl transition-all hover:scale-105"
            title={theme === 'dark' ? "Switch to Light Theme" : "Switch to Dark Theme"}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <FaSun className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <FaMoon className="w-3.5 h-3.5 text-violet-400" />
            )}
          </button>

          {user ? (
            <>
              {/* 24-HOUR ACCESS REWARD BADGE */}
              <div 
                onClick={() => navigate('/profile')} 
                className={`glass-chip px-3 py-1 flex items-center gap-1.5 cursor-pointer text-xs font-bold ${
                  isAccessActive 
                    ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' 
                    : 'text-amber-400 border-amber-500/30 bg-amber-500/10'
                }`}
                title={isAccessActive ? "Unlimited downloads active!" : "Upload a PDF to unlock 24h access"}
              >
                <FaClock className={`w-3 h-3 ${isAccessActive ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
                {user.role === 'admin' ? (
                  <span>Admin Access</span>
                ) : isAccessActive ? (
                  <span>Unlimited ({remainingStr || 'Active'})</span>
                ) : (
                  <span>Unlock 24h Access</span>
                )}
              </div>

              {/* PROFILE BTN */}
              <button
                onClick={() => navigate('/profile')}
                className={`p-2 glass-btn rounded-xl transition-all ${
                  currentPath === '/profile' ? 'bg-violet-600/20 border-violet-500/40 text-violet-400' : ''
                }`}
                title="My Profile & Contributions"
              >
                <FaUser className="w-3.5 h-3.5" />
              </button>

              {/* LOGOUT */}
              <button
                onClick={() => {
                  logout();
                  navigate('/login');
                }}
                className="p-2 glass-btn rounded-xl text-slate-400 hover:text-red-400 transition-all"
                title="Sign Out"
              >
                <FaSignOutAlt className="w-3.5 h-3.5" />
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/login')}
                className="glass-btn px-4 py-1.5 text-xs font-semibold"
              >
                Sign In
              </button>
              <button
                onClick={() => navigate('/register')}
                className="glass-btn-primary px-4 py-1.5 text-xs font-semibold flex items-center gap-1.5"
              >
                <FaMagic className="w-3 h-3" />
                <span>Get Started</span>
              </button>
            </div>
          )}
        </div>

        {/* MOBILE ACTIONS */}
        <div className="md:hidden flex items-center gap-2">
          {/* THEME TOGGLE MOBILE */}
          <button
            onClick={toggleTheme}
            className="p-2 glass-btn rounded-xl"
            title="Toggle theme"
          >
            {theme === 'dark' ? (
              <FaSun className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <FaMoon className="w-3.5 h-3.5 text-violet-400" />
            )}
          </button>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="glass-btn p-2"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <FaTimes className="w-4 h-4" /> : <FaBars className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* MOBILE MENU DRAWER */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-modal mt-2 p-3 space-y-2 animate-fade-in max-w-7xl mx-auto shadow-2xl">
          <button
            onClick={() => { navigate('/library'); setMobileMenuOpen(false); }}
            className="w-full text-left px-3.5 py-2.5 glass-btn font-semibold flex items-center gap-2 text-xs"
          >
            <FaBook className="w-3.5 h-3.5 text-cyan-400" /> 
            <span>Digital Library</span>
          </button>
          <button
            onClick={() => { navigate('/upload'); setMobileMenuOpen(false); }}
            className="w-full text-left px-3.5 py-2.5 glass-btn font-semibold flex items-center gap-2 text-xs"
          >
            <FaCloudUploadAlt className="w-3.5 h-3.5 text-violet-400" /> 
            <span>Upload PDF</span>
          </button>
          {user ? (
            <>
              <button
                onClick={() => { navigate('/profile'); setMobileMenuOpen(false); }}
                className="w-full text-left px-3.5 py-2.5 glass-btn font-semibold flex items-center gap-2 text-xs"
              >
                <FaUser className="w-3.5 h-3.5 text-violet-400" /> 
                <span>Profile & Contributions</span>
              </button>
              {user.role === 'admin' && (
                <button
                  onClick={() => { navigate('/admin'); setMobileMenuOpen(false); }}
                  className="w-full text-left px-3.5 py-2.5 glass-btn font-semibold text-pink-400 flex items-center gap-2 text-xs"
                >
                  <FaUserShield className="w-3.5 h-3.5" /> 
                  <span>Admin Portal</span>
                </button>
              )}
              <button
                onClick={() => { logout(); navigate('/login'); setMobileMenuOpen(false); }}
                className="w-full text-left px-3.5 py-2.5 glass-btn font-semibold text-red-400 flex items-center gap-2 text-xs"
              >
                <FaSignOutAlt className="w-3.5 h-3.5" /> 
                <span>Sign Out</span>
              </button>
            </>
          ) : (
            <div className="pt-1 flex flex-col gap-2">
              <button
                onClick={() => { navigate('/login'); setMobileMenuOpen(false); }}
                className="w-full glass-btn py-2.5 font-semibold text-center text-xs"
              >
                Sign In
              </button>
              <button
                onClick={() => { navigate('/register'); setMobileMenuOpen(false); }}
                className="w-full glass-btn-primary py-2.5 font-semibold text-center text-xs"
              >
                Get Started
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
