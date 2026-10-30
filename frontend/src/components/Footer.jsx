import React from 'react';
import { FaBookOpen, FaUserShield, FaFileAlt, FaCheckCircle } from 'react-icons/fa';

export default function Footer({ navigate }) {
  return (
    <footer className="mt-24 border-t theme-footer pt-16 pb-10 px-4 sm:px-8">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
        
        {/* BRAND COLUMN */}
        <div className="md:col-span-1 space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 via-indigo-600 to-cyan-500 p-0.5 shadow-lg shadow-violet-500/20 flex items-center justify-center">
              <div className="w-full h-full theme-footer-logo-bg rounded-[10px] flex items-center justify-center text-violet-500">
                <FaBookOpen className="w-4 h-4" />
              </div>
            </div>
            <span className="font-black text-xl theme-footer-logo-title">
              Study<span className="bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent">Vault</span>
            </span>
          </div>
          <p className="text-xs theme-footer-text leading-relaxed">
            The student-to-student digital library platform for discovering, sharing, and downloading legitimate study notes, interview resources, and academic materials.
          </p>
          <div className="theme-footer-badge inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold rounded-xl shadow-sm">
            <FaCheckCircle className="w-3.5 h-3.5 flex-shrink-0" /> Share 1 Doc = 24h Unlimited Access
          </div>
        </div>

        {/* POPULAR CATEGORIES */}
        <div className="space-y-3">
          <h4 className="font-bold theme-footer-heading text-sm">Study Categories</h4>
          <ul className="space-y-2 text-xs font-semibold theme-footer-text">
            <li><button onClick={() => navigate('/library?category=cat_1')} className="theme-footer-link flex items-center text-left">B.Tech Semester Notes</button></li>
            <li><button onClick={() => navigate('/library?category=cat_4')} className="theme-footer-link flex items-center text-left">Programming & DSA Guides</button></li>
            <li><button onClick={() => navigate('/library?category=cat_5')} className="theme-footer-link flex items-center text-left">Interview Preparation</button></li>
            <li><button onClick={() => navigate('/library?category=cat_13')} className="theme-footer-link flex items-center text-left">Previous Question Papers</button></li>
          </ul>
        </div>

        {/* QUICK NAVIGATION */}
        <div className="space-y-3">
          <h4 className="font-bold theme-footer-heading text-sm">Platform</h4>
          <ul className="space-y-2 text-xs font-semibold theme-footer-text">
            <li><button onClick={() => navigate('/library')} className="theme-footer-link theme-footer-link-cyan flex items-center text-left">Digital Library</button></li>
            <li><button onClick={() => navigate('/upload')} className="theme-footer-link flex items-center text-left">Upload Document</button></li>
            <li><button onClick={() => navigate('/profile')} className="theme-footer-link flex items-center text-left">My Contributions</button></li>
            <li>
              <button 
                onClick={() => navigate('/admin/login')} 
                className="theme-footer-admin flex items-center gap-1.5 text-xs font-bold transition-colors"
                title="Admin Management Portal"
              >
                <FaUserShield className="w-3.5 h-3.5 flex-shrink-0" />
                <span>Admin Portal</span>
              </button>
            </li>
          </ul>
        </div>

        {/* COPYRIGHT & MODERATION POLICY */}
        <div className="space-y-3">
          <h4 className="font-bold theme-footer-heading text-sm">Copyright & Policy</h4>
          <p className="text-xs theme-footer-text leading-relaxed">
            StudyVault strictly promotes legitimate educational resource sharing. Users must confirm ownership or distribution rights before uploading.
          </p>
          <div className="flex items-center gap-2 text-xs theme-footer-text font-medium">
            <FaFileAlt className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <span>Pirated textbooks & copyrighted content are prohibited.</span>
          </div>
        </div>

      </div>

      <div className="theme-footer-copyright max-w-7xl mx-auto pt-6 border-t flex flex-col sm:flex-row items-center justify-between text-xs gap-4">
        <p>© 2026 StudyVault Digital Library. Built for Students.</p>
        <p className="flex items-center gap-1 font-medium">
          Designed with Glassmorphism & React Icons
        </p>
      </div>
    </footer>
  );
}
