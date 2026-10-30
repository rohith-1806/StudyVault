import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FaBookOpen, 
  FaSearch, 
  FaCloudUploadAlt, 
  FaMagic, 
  FaArrowRight, 
  FaGraduationCap, 
  FaCode, 
  FaBriefcase, 
  FaFileAlt, 
  FaTrophy, 
  FaClock, 
  FaMicrochip, 
  FaBrain, 
  FaBuilding, 
  FaBook, 
  FaSeedling, 
  FaBookReader, 
  FaStar,
  FaCheckCircle 
} from 'react-icons/fa';
import { api } from '../services/api';

const CATEGORY_ICONS = {
  'cat_1': FaGraduationCap,
  'cat_2': FaBookOpen,
  'cat_3': FaMicrochip,
  'cat_4': FaCode,
  'cat_5': FaBriefcase,
  'cat_6': FaBuilding,
  'cat_7': FaBrain,
  'cat_8': FaMagic,
  'cat_9': FaTrophy,
  'cat_13': FaFileAlt,
};

// Subtle background particle positions
const BACKGROUND_PARTICLES = [
  { top: '15%', left: '8%', size: 'w-1.5 h-1.5', color: 'bg-violet-400', delay: '0s' },
  { top: '25%', left: '22%', size: 'w-1 h-1', color: 'bg-cyan-400', delay: '2s' },
  { top: '18%', right: '12%', size: 'w-2 h-2', color: 'bg-indigo-400', delay: '1s' },
  { top: '40%', right: '20%', size: 'w-1 h-1', color: 'bg-cyan-300', delay: '3.5s' },
  { top: '65%', left: '14%', size: 'w-1.5 h-1.5', color: 'bg-violet-300', delay: '1.5s' },
  { top: '55%', right: '10%', size: 'w-1 h-1', color: 'bg-violet-400', delay: '4s' },
  { top: '75%', right: '28%', size: 'w-1.5 h-1.5', color: 'bg-cyan-400', delay: '2.5s' },
  { top: '32%', left: '50%', size: 'w-1 h-1', color: 'bg-indigo-300', delay: '3s' },
];

export default function LandingHome({ navigate }) {
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  // Hero mouse offset for ambient parallax
  const [heroMouse, setHeroMouse] = useState({ x: 0, y: 0 });
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [searchSpotlight, setSearchSpotlight] = useState({ x: -100, y: -100, active: false });

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await api.getDocuments({ limit: 1 });
        setCategories(res.categories || []);
      } catch (err) {
        console.error('Failed to load homepage resources:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleHeroMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width - 0.5) * 35;
    const y = ((e.clientY - rect.top) / rect.height - 0.5) * 35;
    setHeroMouse({ x, y });
  };

  const handleSearchMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setSearchSpotlight({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      active: true
    });
  };

  const handleSearchMouseLeave = () => {
    setSearchSpotlight(prev => ({ ...prev, active: false }));
  };

  const handleSearchSubmit = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const query = searchQuery.trim();
    if (query) {
      navigate(`/library?search=${encodeURIComponent(query)}`);
    } else {
      navigate('/library');
    }
  };

  return (
    <div className="space-y-12 sm:space-y-16 pb-14 relative overflow-x-hidden">
      
      {/* --- AMBIENT BACKGROUND GLOW LIGHT ORBS WITH PARALLAX --- */}
      <div 
        className="absolute top-10 left-[8%] w-[500px] h-[500px] bg-violet-600/18 rounded-full blur-[140px] pointer-events-none animate-orb-slow transition-transform duration-700 ease-out"
        style={{
          transform: `translate3d(${heroMouse.x * 0.9}px, ${heroMouse.y * 0.9}px, 0)`
        }}
      />
      <div 
        className="absolute top-16 right-[6%] w-[450px] h-[450px] bg-cyan-500/18 rounded-full blur-[130px] pointer-events-none animate-orb-reverse transition-transform duration-700 ease-out"
        style={{
          transform: `translate3d(${-heroMouse.x * 0.8}px, ${-heroMouse.y * 0.8}px, 0)`
        }}
      />
      <div 
        className="absolute top-44 left-1/2 -translate-x-1/2 w-[380px] h-[380px] bg-indigo-500/10 rounded-full blur-[130px] pointer-events-none"
      />

      {/* --- SUBTLE BACKGROUND FLOATING PARTICLES --- */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        {BACKGROUND_PARTICLES.map((p, idx) => (
          <div
            key={idx}
            className={`absolute rounded-full ${p.size} ${p.color} animate-particle-drift opacity-30 shadow-[0_0_8px_currentColor]`}
            style={{
              top: p.top,
              left: p.left,
              right: p.right,
              animationDelay: p.delay
            }}
          />
        ))}
      </div>

      {/* --- HERO SECTION --- */}
      <section 
        onMouseMove={handleHeroMouseMove}
        className="relative pt-10 sm:pt-14 pb-8 sm:pb-12 px-4 sm:px-6 overflow-visible"
      >
        
        {/* DECORATIVE FLOATING GLASS DOCUMENT CARDS (WIDE DESKTOP ONLY TO PREVENT ANY OVERLAP) */}
        <div 
          className="hidden 2xl:flex flex-col gap-3 absolute left-6 2xl:left-10 top-1/2 -translate-y-1/2 pointer-events-none z-10 animate-float-gentle"
          aria-hidden="true"
        >
          <div className="glass-card p-3.5 backdrop-blur-xl border border-white/10 shadow-xl max-w-[210px] transition-all duration-300">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-7 h-7 rounded-lg bg-violet-500/20 text-violet-400 flex items-center justify-center">
                <FaBookOpen className="w-3.5 h-3.5" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wider">Curated</span>
                <p className="text-xs font-bold truncate max-w-[125px]">OS Lecture Notes</p>
              </div>
            </div>
            <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-white/5">
              <span className="flex items-center gap-1 text-amber-400 font-semibold">
                <FaStar className="w-2.5 h-2.5" /> 4.9 Rating
              </span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <FaCheckCircle className="w-2.5 h-2.5" /> Verified
              </span>
            </div>
          </div>
        </div>

        <div 
          className="hidden 2xl:flex flex-col gap-3 absolute right-6 2xl:right-10 top-1/2 -translate-y-1/2 pointer-events-none z-10 animate-float-reverse"
          aria-hidden="true"
        >
          <div className="glass-card p-3.5 backdrop-blur-xl border border-white/10 shadow-xl max-w-[210px] transition-all duration-300">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
                <FaMicrochip className="w-3.5 h-3.5" />
              </div>
              <div>
                <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Trending</span>
                <p className="text-xs font-bold truncate max-w-[125px]">DSA PYQ Collection</p>
              </div>
            </div>
            <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-white/5">
              <span className="flex items-center gap-1 text-cyan-400 font-semibold">
                <FaFileAlt className="w-2.5 h-2.5" /> 24h Access
              </span>
              <span className="text-violet-400 font-semibold flex items-center gap-1">
                <FaStar className="w-2.5 h-2.5" /> 5.0 Star
              </span>
            </div>
          </div>
        </div>

        {/* HERO MAIN CONTENT */}
        <div className="max-w-4xl mx-auto text-center relative z-20 space-y-5 sm:space-y-6 overflow-visible">
          
          {/* BADGE CHIP */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 glass-chip px-3.5 py-1.5 text-xs font-semibold text-violet-400 bg-violet-500/10 border-violet-500/30 hover:border-violet-500/50 transition-colors cursor-default"
          >
            <FaMagic className="w-3.5 h-3.5 text-violet-400 animate-pulse" />
            <span>Next-Gen Student Knowledge Platform</span>
          </motion.div>

          {/* HERO HEADING WITH STAGGERED ENTRANCE & SHIMMER */}
          <div className="space-y-1 sm:space-y-2 overflow-visible">
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.25] sm:leading-[1.22] lg:leading-[1.2] select-text overflow-visible pb-1 sm:pb-2"
            >
              <span className="inline-block overflow-visible">Your Campus Knowledge.</span>
              <br />
              <motion.span 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
                className="inline-block text-shimmer overflow-visible hover:scale-[1.01] transition-transform duration-300"
              >
                One Digital Library.
              </motion.span>
            </motion.h1>
          </div>

          <motion.p 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.25 }}
            className="text-sm sm:text-lg text-slate-400 max-w-2xl mx-auto font-normal leading-relaxed"
          >
            Discover verified lecture notes, interview prep materials, previous papers, and skill guides shared by students.
          </motion.p>

          {/* --- INTERACTIVE SEARCH BOX WITH SPOTLIGHT & GLOW --- */}
          <motion.form 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.35 }}
            onSubmit={handleSearchSubmit}
            className="max-w-2xl mx-auto pt-2"
          >
            <div 
              onMouseMove={handleSearchMouseMove}
              onMouseLeave={handleSearchMouseLeave}
              className={`search-glow-container glass-card p-2 sm:p-2.5 flex items-center gap-2 shadow-2xl relative overflow-hidden transition-all duration-300 ${
                isSearchFocused ? 'ring-2 ring-violet-500/40 border-violet-400/60 shadow-[0_0_30px_rgba(139,92,246,0.35)]' : ''
              }`}
            >
              {/* MOUSE-RESPONSIVE SPOTLIGHT OVERLAY */}
              {searchSpotlight.active && (
                <div 
                  className="absolute inset-0 pointer-events-none transition-opacity duration-300"
                  style={{
                    background: `radial-gradient(circle 160px at ${searchSpotlight.x}px ${searchSpotlight.y}px, rgba(139, 92, 246, 0.18), transparent 70%)`
                  }}
                  aria-hidden="true"
                />
              )}

              {/* SEARCH ICON BUTTON WITH DYNAMIC FOCUS/HOVER RESPONSE */}
              <button
                type="submit"
                className={`p-2 transition-all duration-300 flex-shrink-0 relative z-10 ${
                  isSearchFocused 
                    ? 'text-cyan-400 scale-110 rotate-6 drop-shadow-[0_0_8px_rgba(34,211,238,0.7)]' 
                    : 'text-violet-400 hover:text-violet-300 hover:scale-105'
                }`}
                title="Search"
                aria-label="Search documents"
              >
                <FaSearch className="w-4 h-4" />
              </button>

              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearchSubmit(e);
                  }
                }}
                placeholder="Search notes, DV, Quantum, Operating Systems, PYQs..."
                className="w-full bg-transparent text-xs sm:text-sm font-semibold placeholder-slate-400 focus:outline-none px-1 relative z-10"
              />

              {/* SEARCH ACTION BUTTON WITH MICRO-INTERACTION */}
              <button
                type="submit"
                className="group glass-btn-primary px-5 sm:px-6 py-2.5 text-xs sm:text-sm font-bold flex items-center gap-2 flex-shrink-0 relative z-10 hover:-translate-y-0.5 active:scale-95 transition-all duration-200"
              >
                <span>Search</span>
                <FaArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform duration-200" />
              </button>
            </div>
          </motion.form>

          {/* --- CTA BUTTONS WITH PREMIUM MICRO-INTERACTIONS --- */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.45 }}
            className="flex flex-wrap items-center justify-center gap-3 pt-2"
          >
            {/* EXPLORE LIBRARY BUTTON */}
            <button
              onClick={() => navigate('/library')}
              className="group glass-btn-primary px-6 py-3 text-xs sm:text-sm font-bold flex items-center gap-2 hover:-translate-y-0.5 hover:shadow-[0_10px_25px_rgba(139,92,246,0.5)] active:scale-95 transition-all duration-200"
            >
              <span>Explore Library</span>
              <FaArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1.5 transition-transform duration-200" />
            </button>

            {/* UPLOAD RESOURCE BUTTON */}
            <button
              onClick={() => navigate('/upload')}
              className="group glass-btn px-6 py-3 text-xs sm:text-sm font-bold flex items-center gap-2 hover:text-violet-400 hover:border-violet-500/40 hover:bg-violet-500/10 hover:-translate-y-0.5 active:scale-95 transition-all duration-200"
            >
              <FaCloudUploadAlt className="w-4 h-4 text-violet-400 group-hover:-translate-y-0.5 group-hover:scale-110 transition-transform duration-200" />
              <span>Upload a Resource</span>
            </button>
          </motion.div>

          {/* FAIR ACCESS MODEL NOTICE */}
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.55 }}
            className="pt-2"
          >
            <div className="glass-card inline-flex items-center gap-2.5 px-4 py-2 text-xs font-medium border-emerald-500/30 bg-emerald-500/10 shadow-sm hover:border-emerald-500/50 transition-colors">
              <FaClock className="w-3.5 h-3.5 text-emerald-400 animate-pulse flex-shrink-0" />
              <span>
                <strong className="text-emerald-400 font-bold">24-Hour Fair Access Model:</strong> Share 1 valid study PDF to unlock 24 hours of unlimited downloads!
              </span>
            </div>
          </motion.div>

        </div>
      </section>

      {/* --- POPULAR CATEGORIES (WITH ENTRANCE ANIMATION & SPOTLIGHT HOVER) --- */}
      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.1, ease: 'easeOut' }}
        className="max-w-7xl mx-auto px-4 sm:px-6"
      >
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight">Popular Resource Categories</h2>
            <p className="text-xs text-slate-400 font-normal">Browse verified educational materials by domain</p>
          </div>
          <button
            onClick={() => navigate('/library')}
            className="group glass-btn px-3.5 py-1.5 text-xs font-semibold text-violet-400 hover:text-violet-300 flex items-center gap-1.5 active:scale-95 transition-all"
          >
            <span>View All</span>
            <FaArrowRight className="w-2.5 h-2.5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
          {categories.slice(0, 10).map((cat) => {
            const IconComp = CATEGORY_ICONS[cat.id] || FaBook;
            return (
              <div
                key={cat.id}
                onClick={() => navigate(`/library?category=${cat.id}`)}
                className="group glass-card glass-card-hover p-3.5 cursor-pointer text-center flex flex-col items-center justify-center space-y-2 hover:-translate-y-1 hover:border-violet-500/40 transition-all duration-300"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600/20 to-cyan-500/20 border border-white/10 flex items-center justify-center text-cyan-400 group-hover:scale-110 group-hover:text-cyan-300 transition-all duration-300">
                  <IconComp className="w-4 h-4" />
                </div>
                <h3 className="font-semibold text-xs sm:text-sm truncate max-w-full group-hover:text-violet-400 transition-colors">{cat.name}</h3>
                <p className="text-[11px] text-slate-400 line-clamp-1">{cat.description}</p>
              </div>
            );
          })}
        </div>
      </motion.section>

      {/* --- TOP CONTRIBUTORS GAMIFICATION --- */}
      <motion.section 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.2, ease: 'easeOut' }}
        className="max-w-7xl mx-auto px-4 sm:px-6"
      >
        <div className="glass-card p-6 sm:p-8 relative overflow-hidden shadow-xl hover:border-violet-500/30 transition-all duration-300">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center relative z-10">
            <div className="space-y-2">
              <span className="glass-chip px-3 py-1 text-[11px] font-bold text-violet-400 bg-violet-500/15 border-violet-500/30">
                Community Gamification
              </span>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight">Student Knowledge Exchange</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Join thousands of students sharing semester notes, viva questions, PYQs, and placement guides.
              </p>
            </div>

            <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="group glass-pressed p-3.5 rounded-xl text-center flex flex-col items-center justify-center space-y-1 hover:border-emerald-500/40 hover:-translate-y-1 transition-all duration-300 cursor-default">
                <FaSeedling className="w-6 h-6 text-emerald-400 mb-1 group-hover:scale-110 transition-transform" />
                <h4 className="font-semibold text-xs mt-1">New Contributor</h4>
                <p className="text-[10px] text-slate-400">1 Valid Upload</p>
              </div>
              <div className="group glass-pressed p-3.5 rounded-xl text-center flex flex-col items-center justify-center space-y-1 hover:border-cyan-500/40 hover:-translate-y-1 transition-all duration-300 cursor-default">
                <FaBookReader className="w-6 h-6 text-cyan-400 mb-1 group-hover:scale-110 transition-transform" />
                <h4 className="font-semibold text-xs mt-1">Active Contributor</h4>
                <p className="text-[10px] text-slate-400">3+ Uploads</p>
              </div>
              <div className="group glass-pressed p-3.5 rounded-xl text-center flex flex-col items-center justify-center space-y-1 hover:border-amber-500/40 hover:-translate-y-1 transition-all duration-300 cursor-default">
                <FaStar className="w-6 h-6 text-amber-400 mb-1 group-hover:scale-110 transition-transform" />
                <h4 className="font-semibold text-xs mt-1">Knowledge Star</h4>
                <p className="text-[10px] text-slate-400">10+ Uploads</p>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

    </div>
  );
}
