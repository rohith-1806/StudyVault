import React, { useState, useEffect } from 'react';
import { 
  FaSearch, 
  FaFilter, 
  FaSlidersH, 
  FaBookOpen, 
  FaRedo, 
  FaTimes, 
  FaExclamationTriangle 
} from 'react-icons/fa';
import { api } from '../services/api';
import DocumentCard from '../components/DocumentCard';

/**
 * Filter documents ensuring only genuine matches are displayed.
 * Discards low-relevance word overlap when a specific phrase or high-relevance match exists.
 */
export function filterDocuments(documents, search, selectedCategory, courseFilter) {
  let list = documents || [];

  if (selectedCategory) {
    list = list.filter(d => d.category_id === selectedCategory || d.category_slug === selectedCategory);
  }

  if (courseFilter && courseFilter.trim()) {
    const cf = courseFilter.trim().toLowerCase();
    list = list.filter(d => (d.course || '').toLowerCase().includes(cf));
  }

  if (!search || !search.trim()) {
    return list;
  }

  const q = search.trim().toLowerCase();
  const words = q.split(/\s+/).map(w => w.trim()).filter(w => w.length > 0);
  if (words.length === 0) return list;

  const scored = [];
  for (const doc of list) {
    const title = (doc.title || '').toLowerCase();
    const subject = (doc.subject || '').toLowerCase();
    const course = (doc.course || '').toLowerCase();
    const desc = (doc.description || '').toLowerCase();
    const tags = (doc.tags || '').toLowerCase();
    const allFields = [title, subject, course, desc, tags];

    let score = 0;
    if (title === q || subject === q) {
      score = 100;
    } else if (title.includes(q) || subject.includes(q)) {
      score = 90;
    } else if (allFields.some(f => f.includes(q))) {
      score = 80;
    } else {
      const matchedWords = words.filter(w => allFields.some(f => f.includes(w)));
      if (matchedWords.length > 0) {
        score = (matchedWords.length / words.length) * 70;
      }
    }

    if (score > 0) {
      scored.push({ doc, score });
    }
  }

  if (scored.length === 0) return [];

  const maxScore = Math.max(...scored.map(s => s.score));
  const threshold = maxScore >= 80 ? 60 : Math.max(35, maxScore * 0.7);

  return scored.filter(s => s.score >= threshold).map(s => s.doc);
}

export default function DigitalLibrary({ initialSearch = '', initialCategory = '', navigate, onPreview, onDownload, onOpenSummary }) {
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState(initialSearch);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [courseFilter, setCourseFilter] = useState('');
  const [sortBy, setSortBy] = useState('latest');
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [page, setPage] = useState(1);

  // Sync state if initialSearch or initialCategory prop changes
  useEffect(() => {
    setSearch(initialSearch);
    setSelectedCategory(initialCategory);
  }, [initialSearch, initialCategory]);

  // Keep browser URL synchronized with current search without reloads
  useEffect(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set('search', search.trim());
    if (selectedCategory) params.set('category', selectedCategory);
    const queryString = params.toString();
    const newUrl = queryString ? `/library?${queryString}` : '/library';
    if (window.location.pathname + window.location.search !== newUrl) {
      window.history.replaceState({}, '', newUrl);
    }
  }, [search, selectedCategory]);

  const loadDocuments = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const res = await api.getDocuments({
        category: selectedCategory,
        search: search.trim(),
        course: courseFilter.trim(),
        sort_by: sortBy,
        page: page,
        limit: 50
      });
      setDocuments(res.documents || []);
      setCategories(res.categories || []);
    } catch (err) {
      console.error('Failed to load library resources:', err);
      setApiError(err.message || 'Unable to connect to the library server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadDocuments();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, selectedCategory, courseFilter, sortBy, page]);

  // Synchronize document view count updates in real-time
  useEffect(() => {
    const handleDocViewUpdate = (e) => {
      const { docId, viewsCount } = e.detail || {};
      if (docId) {
        setDocuments(prev => prev.map(d => (d.id === docId ? { ...d, views_count: viewsCount } : d)));
      }
    };
    window.addEventListener('studyvault:doc-view-updated', handleDocViewUpdate);
    return () => window.removeEventListener('studyvault:doc-view-updated', handleDocViewUpdate);
  }, []);

  const handleClearSearch = () => {
    setSearch('');
    setSelectedCategory('');
    setCourseFilter('');
    setPage(1);
    window.history.replaceState({}, '', '/library');
  };

  const filteredDocuments = filterDocuments(documents, search, selectedCategory, courseFilter);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      
      {/* PAGE TITLE */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Explore the Library</h1>
          <p className="text-xs text-slate-400 font-medium mt-0.5">Discover verified educational PDFs shared by students nationwide</p>
        </div>
        <div className="glass-chip px-3.5 py-1.5 text-xs font-bold text-violet-400 bg-violet-500/15 border-violet-500/30 self-start sm:self-auto">
          {filteredDocuments.length} {filteredDocuments.length === 1 ? 'Resource' : 'Resources'} Found
        </div>
      </div>

      {/* SEARCH BAR & FILTERS HEADER */}
      <div className="space-y-3.5">
        <div className="glass-card p-2.5 sm:p-3 flex flex-col sm:flex-row items-center gap-2.5 shadow-lg">
          
          {/* SEARCH INPUT */}
          <div className="flex-1 flex items-center w-full px-3 py-2 glass-pressed rounded-xl">
            <FaSearch className="w-3.5 h-3.5 text-violet-400 mr-2 flex-shrink-0" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search title, DV, Quantum, subject, course, or tags..."
              className="w-full bg-transparent text-xs font-semibold placeholder-slate-400 focus:outline-none"
            />
            {search && (
              <button 
                onClick={() => { setSearch(''); setPage(1); }}
                className="p-1 hover:text-red-400 text-slate-400 transition-colors"
                title="Clear input"
              >
                <FaTimes className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* COURSE FILTER INPUT */}
          <div className="w-full sm:w-44 glass-pressed px-3 py-2 rounded-xl flex items-center">
            <FaFilter className="w-3 h-3 text-cyan-400 mr-2 flex-shrink-0" />
            <input
              type="text"
              value={courseFilter}
              onChange={(e) => { setCourseFilter(e.target.value); setPage(1); }}
              placeholder="Course (e.g. CSE)"
              className="w-full bg-transparent text-xs font-semibold placeholder-slate-400 focus:outline-none"
            />
          </div>

          {/* SORT BY DROPDOWN */}
          <div className="w-full sm:w-44 glass-pressed px-3 py-2 rounded-xl flex items-center">
            <FaSlidersH className="w-3.5 h-3.5 text-violet-400 mr-2 flex-shrink-0" />
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
              className="w-full bg-transparent text-xs font-semibold focus:outline-none cursor-pointer"
            >
              <option value="latest">Sort by Latest</option>
              <option value="popular">Sort by Popular</option>
              <option value="downloads">Sort by Downloads</option>
            </select>
          </div>

        </div>

        {/* CATEGORY CHIPS SCROLLABLE ROW */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1.5 no-scrollbar max-w-full">
          <button
            onClick={() => { setSelectedCategory(''); setPage(1); }}
            className={`glass-chip px-3 py-1.5 text-xs font-semibold whitespace-nowrap flex-shrink-0 transition-all ${
              selectedCategory === '' ? 'glass-chip-active' : 'hover:scale-105'
            }`}
          >
            All Categories
          </button>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => { setSelectedCategory(cat.id); setPage(1); }}
              className={`glass-chip px-3 py-1.5 text-xs font-semibold whitespace-nowrap flex-shrink-0 transition-all ${
                selectedCategory === cat.id ? 'glass-chip-active' : 'hover:scale-105'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      {/* DOCUMENT GRID & STATES */}
      {/* 1. API LOADING STATE */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map(n => (
            <div key={n} className="glass-card p-4 h-56 animate-pulse space-y-3">
              <div className="w-20 h-4 bg-slate-700/40 rounded" />
              <div className="w-40 h-5 bg-slate-700/40 rounded" />
              <div className="w-full h-10 bg-slate-800/40 rounded" />
              <div className="w-full h-8 bg-slate-700/40 rounded mt-auto" />
            </div>
          ))}
        </div>
      ) : apiError ? (
        /* 2. API ERROR STATE (Proper error message, not No Files Found) */
        <div className="glass-card p-10 sm:p-14 text-center max-w-lg mx-auto my-10 space-y-4 shadow-xl">
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 mx-auto flex items-center justify-center">
            <FaExclamationTriangle className="w-7 h-7" />
          </div>
          <div>
            <h3 className="font-extrabold text-xl tracking-tight">Failed to Load Documents</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed max-w-sm mx-auto">
              {apiError}
            </p>
          </div>
          <button
            onClick={loadDocuments}
            className="glass-btn-primary px-5 py-2.5 text-xs font-semibold flex items-center gap-2 mx-auto transition-transform hover:scale-105"
          >
            <FaRedo className="w-3 h-3" /> Retry Loading
          </button>
        </div>
      ) : filteredDocuments.length === 0 ? (
        /* 3. ZERO RESULTS EMPTY STATE */
        <div className="glass-card p-10 sm:p-14 text-center max-w-lg mx-auto my-10 space-y-4 shadow-xl">
          <div className="w-14 h-14 rounded-2xl bg-violet-500/10 border border-violet-500/20 text-violet-400 mx-auto flex items-center justify-center">
            <FaBookOpen className="w-7 h-7" />
          </div>
          <div>
            <h3 className="font-extrabold text-xl tracking-tight">No Files Found</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed max-w-sm mx-auto">
              {search.trim() 
                ? `We couldn't find any documents matching "${search.trim()}". Try another keyword or clear your search.`
                : "We couldn't find any documents matching your active filters. Try another keyword or clear your filters."}
            </p>
          </div>
          <button
            onClick={handleClearSearch}
            className="glass-btn-primary px-5 py-2.5 text-xs font-semibold flex items-center gap-2 mx-auto transition-transform hover:scale-105"
          >
            <FaRedo className="w-3 h-3" /> Clear Search
          </button>
        </div>
      ) : (
        /* 4. RENDER MATCHING DOCUMENT CARDS */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocuments.map(doc => (
            <DocumentCard
              key={doc.id}
              doc={doc}
              onPreview={onPreview}
              onDownload={onDownload}
              onOpenSummary={onOpenSummary}
              navigate={navigate}
            />
          ))}
        </div>
      )}

    </div>
  );
}
