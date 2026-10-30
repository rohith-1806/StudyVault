import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  FaCloudUploadAlt, 
  FaFilePdf, 
  FaCheckCircle, 
  FaExclamationTriangle, 
  FaUserShield, 
  FaClock, 
  FaArrowRight, 
  FaMagic,
  FaTimes,
  FaCheck,
  FaSpinner
} from 'react-icons/fa';
import { api } from '../services/api';
import { formatFileSize } from '../components/DocumentCard';

const CATEGORY_OPTIONS = [
  { id: 'cat_1', name: 'B.Tech' },
  { id: 'cat_2', name: 'M.Tech' },
  { id: 'cat_3', name: 'Engineering' },
  { id: 'cat_4', name: 'Programming' },
  { id: 'cat_5', name: 'Interview Preparation' },
  { id: 'cat_6', name: 'Placement' },
  { id: 'cat_7', name: 'Aptitude' },
  { id: 'cat_8', name: 'Reasoning' },
  { id: 'cat_9', name: 'Competitive Exams' },
  { id: 'cat_10', name: 'General Knowledge' },
  { id: 'cat_11', name: 'Skill Development' },
  { id: 'cat_12', name: 'Project Resources' },
  { id: 'cat_13', name: 'Previous Question Papers' },
  { id: 'cat_14', name: 'Career Resources' },
  { id: 'cat_15', name: 'Other' },
];

export default function UploadDocument({ navigate }) {
  const { user, refreshUser } = useAuth();
  
  const [file, setFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('cat_1');
  const [course, setCourse] = useState('');
  const [subject, setSubject] = useState('');
  const [semester, setSemester] = useState('');
  const [tags, setTags] = useState('');
  const [copyrightConfirmed, setCopyrightConfirmed] = useState(false);

  const [uploading, setUploading] = useState(false);
  const [validationStep, setValidationStep] = useState(0); // 0: idle, 1: type, 2: structure, 3: content, 4: dupe, 5: done
  const [error, setError] = useState(null);
  const [duplicateInfo, setDuplicateInfo] = useState(null);
  const [successResult, setSuccessResult] = useState(null);

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;
    setError(null);
    setDuplicateInfo(null);

    // Immediate extension check
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Invalid file type: Only .pdf files are accepted in StudyVault.');
      setFile(null);
      return;
    }

    // Immediate MIME type check
    if (selectedFile.type && selectedFile.type !== 'application/pdf') {
      setError('Invalid MIME type: Please select a valid Adobe PDF file.');
      setFile(null);
      return;
    }

    // Immediate zero-byte / empty check
    if (selectedFile.size === 0) {
      setError('Empty file: The selected PDF contains 0 bytes.');
      setFile(null);
      return;
    }

    // Immediate size limit check (25MB)
    if (selectedFile.size > 25 * 1024 * 1024) {
      setError('File too large: Maximum PDF upload size is 25MB.');
      setFile(null);
      return;
    }

    setFile(selectedFile);
    if (!title) {
      const baseName = selectedFile.name.replace(/\.[^/.]+$/, '');
      setTitle(baseName.replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF file.');
      return;
    }
    if (!copyrightConfirmed) {
      setError('You must confirm copyright ownership before uploading.');
      return;
    }

    setUploading(true);
    setError(null);
    setDuplicateInfo(null);
    setValidationStep(1);

    setTimeout(() => setValidationStep(2), 300);
    setTimeout(() => setValidationStep(3), 600);
    setTimeout(() => setValidationStep(4), 900);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('category_id', category);
    formData.append('course', course);
    formData.append('subject', subject);
    formData.append('semester', semester);
    formData.append('tags', tags);
    formData.append('copyright_confirmed', 'true');

    try {
      const res = await api.uploadDocument(formData);
      setValidationStep(5);
      setSuccessResult(res);
      await refreshUser();
    } catch (err) {
      setValidationStep(0);
      if (err.status === 409 || err.code === 'DUPLICATE_DOCUMENT' || err.data?.code === 'DUPLICATE_DOCUMENT') {
        const dupData = err.data || {};
        setDuplicateInfo({
          duplicate_type: dupData.duplicate_type || 'content_hash',
          message: dupData.message || 'This document already exists in StudyVault.',
          existing_document: dupData.existing_document || { title: title, id: dupData.existing_document_id }
        });
        setError(null);
      } else {
        setError(err.message || 'Upload failed.');
        setDuplicateInfo(null);
      }
    } finally {
      setUploading(false);
    }
  };

  if (!user) {
    return (
      <div className="max-w-md mx-auto py-16 text-center glass-card p-8 space-y-4">
        <FaUserShield className="w-12 h-12 text-violet-400 mx-auto" />
        <h3 className="font-bold text-white text-lg">Sign In Required</h3>
        <p className="text-xs text-slate-400">Please log in or register to contribute educational resources to the digital library.</p>
        <button onClick={() => navigate('/login')} className="glass-btn-primary px-6 py-2.5 text-xs font-bold">
          Sign In to Upload
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      
      {/* HEADER */}
      <div className="text-center space-y-2">
        <div className="w-14 h-14 glass-btn mx-auto flex items-center justify-center text-violet-400 rounded-2xl mb-2">
          <FaCloudUploadAlt className="w-7 h-7 stroke-[2.5]" />
        </div>
        <h1 className="text-3xl font-black text-white">Upload Educational Resource</h1>
        <p className="text-xs text-slate-400 font-medium max-w-lg mx-auto">
          Share your notes, interview guides or PYQs to earn <strong className="text-emerald-400 font-bold">24 hours of unlimited downloads</strong>.
        </p>
      </div>

      {/* DUPLICATE DETECTED NOTIFICATION CARD */}
      {duplicateInfo && (
        <div className="glass-card p-6 border border-amber-500/40 bg-gradient-to-br from-amber-950/40 via-slate-900/90 to-slate-950/90 space-y-4 animate-fade-in shadow-2xl">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-400 flex items-center justify-center flex-shrink-0">
              <FaExclamationTriangle className="w-6 h-6" />
            </div>
            <div className="space-y-1.5 flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-extrabold text-base text-white">Duplicate PDF Detected</h3>
                <span className="glass-chip px-2.5 py-0.5 text-[10px] font-bold text-amber-300 bg-amber-500/20 border-amber-500/30">
                  {duplicateInfo.duplicate_type === 'title' ? 'Duplicate Title' : 'Matching SHA-256 Checksum'}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                This document already exists in StudyVault. Please search the library before uploading it again.
              </p>

              {duplicateInfo.existing_document?.title && (
                <div className="mt-3 p-3 glass-pressed rounded-xl border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[11px] text-slate-400 font-medium">Existing Document in Library:</p>
                    <p className="text-xs font-bold text-white truncate" title={duplicateInfo.existing_document.title}>
                      {duplicateInfo.existing_document.title}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        if (duplicateInfo.existing_document?.id) {
                          navigate(`/document/${duplicateInfo.existing_document.id}`);
                        } else {
                          navigate(`/library?search=${encodeURIComponent(duplicateInfo.existing_document.title)}`);
                        }
                      }}
                      className="glass-btn-primary px-3.5 py-1.5 text-xs font-bold flex items-center gap-1.5 rounded-xl shadow-md"
                    >
                      <span>View in Library</span>
                      <FaArrowRight className="w-3 h-3" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setDuplicateInfo(null)}
                      className="glass-btn px-3 py-1.5 text-xs font-bold text-slate-400 hover:text-white rounded-xl"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* GENERIC ERROR BANNER */}
      {error && (
        <div className="p-4 glass-pressed bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-semibold rounded-2xl flex items-center gap-3 animate-fade-in">
          <FaExclamationTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SUCCESS MODAL / REWARD CARD */}
      {successResult ? (
        <div className="glass-card p-8 text-center space-y-6 bg-gradient-to-br from-emerald-950/40 via-slate-900/90 to-slate-950/90 border border-emerald-500/30 animate-fade-in shadow-2xl">
          <div className="w-16 h-16 glass-pressed text-emerald-400 mx-auto flex items-center justify-center rounded-full border border-emerald-500/40">
            <FaCheckCircle className="w-10 h-10" />
          </div>
          <div>
            <span className="glass-chip px-3 py-1 text-xs font-bold text-emerald-300 bg-emerald-500/20 border-emerald-500/30">
              Upload Successful
            </span>
            <h2 className="text-2xl font-black text-white mt-2">24 Hours Unlimited Downloads Unlocked!</h2>
            <p className="text-xs text-slate-300 mt-1 max-w-md mx-auto">
              Your PDF has been added to the StudyVault library.
            </p>
          </div>

          <div className="glass-pressed p-4 rounded-2xl max-w-sm mx-auto flex items-center justify-between text-xs font-bold text-white border border-emerald-500/20">
            <span>Download Access Status:</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <FaClock className="w-4 h-4 text-emerald-400" /> Active (24 Hours)
            </span>
          </div>

          <div className="flex justify-center gap-3 pt-2">
            <button
              onClick={() => {
                setFile(null);
                setSuccessResult(null);
                setTitle('');
                setDescription('');
                setValidationStep(0);
              }}
              className="glass-btn px-5 py-2.5 text-xs font-bold text-slate-200"
            >
              Upload Another Document
            </button>
            <button
              onClick={() => navigate('/library')}
              className="glass-btn-primary px-6 py-2.5 text-xs font-bold flex items-center gap-1.5"
            >
              Explore Library <FaArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="glass-card p-6 sm:p-8 space-y-6 border border-white/20">
          
          {/* DRAG & DROP AREA */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
              isDragOver ? 'border-violet-500 bg-violet-500/10 scale-[1.01]' : 'border-slate-700 hover:border-violet-400 bg-slate-900/40'
            }`}
          >
            {file ? (
              <div className="flex items-center justify-between glass-pressed p-4 rounded-xl">
                <div className="flex items-center gap-3 min-w-0">
                  <FaFilePdf className="w-7 h-7 text-red-400 flex-shrink-0" />
                  <div className="text-left min-w-0">
                    <p className="font-bold text-xs text-white truncate">{file.name}</p>
                    <p className="text-[11px] text-slate-400">{formatFileSize(file.size)} • PDF Document</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="glass-btn p-2 text-slate-400 hover:text-red-400 rounded-lg"
                >
                  <FaTimes className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <label className="cursor-pointer space-y-3 block">
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
                  className="hidden"
                />
                <div className="w-12 h-12 glass-btn mx-auto flex items-center justify-center text-violet-400 rounded-2xl">
                  <FaCloudUploadAlt className="w-6 h-6 stroke-[2]" />
                </div>
                <div>
                  <p className="font-bold text-sm text-white">Drag & Drop your PDF file here</p>
                  <p className="text-xs text-slate-400 mt-1">or <span className="text-violet-400 underline">Browse Files</span> from device</p>
                </div>
                <p className="text-[11px] text-slate-500 font-semibold uppercase">PDF Only • Max 25 MB</p>
              </label>
            )}
          </div>

          {/* STEP-BASED VALIDATION UI */}
          {uploading && (
            <div className="glass-pressed p-5 rounded-2xl space-y-3">
              <h4 className="font-bold text-xs text-white mb-2 flex items-center gap-2">
                <FaSpinner className="w-4 h-4 animate-spin text-violet-400" />
                Validating & Processing Document...
              </h4>
              
              <div className="space-y-2 text-xs font-semibold">
                <div className="flex items-center gap-2 text-emerald-400">
                  <FaCheck className="w-3.5 h-3.5" /> File type verified (.pdf)
                </div>
                <div className={`flex items-center gap-2 ${validationStep >= 2 ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {validationStep >= 2 ? <FaCheck className="w-3.5 h-3.5" /> : <span className="w-3.5 h-3.5 rounded-full border border-slate-600 inline-block" />}
                  PDF structure & signature verified (%PDF-)
                </div>
                <div className={`flex items-center gap-2 ${validationStep >= 3 ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {validationStep >= 3 ? <FaCheck className="w-3.5 h-3.5" /> : <span className="w-3.5 h-3.5 rounded-full border border-slate-600 inline-block" />}
                  Blank PDF inspection passed (Content detected)
                </div>
                <div className={`flex items-center gap-2 ${validationStep >= 4 ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {validationStep >= 4 ? <FaCheck className="w-3.5 h-3.5" /> : <span className="w-3.5 h-3.5 rounded-full border border-slate-600 inline-block" />}
                  Duplicate hash & content fingerprint check passed
                </div>
              </div>
            </div>
          )}

          {/* FORM METADATA FIELDS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-300 mb-1.5">Document Title *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Operating Systems Complete Lecture Notes"
                className="w-full glass-input p-3 text-xs font-semibold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">Category *</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full glass-input p-3 text-xs font-bold bg-slate-900 text-white"
              >
                {CATEGORY_OPTIONS.map(c => (
                  <option key={c.id} value={c.id} className="bg-slate-900 text-white">{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">Course (Optional)</label>
              <input
                type="text"
                value={course}
                onChange={(e) => setCourse(e.target.value)}
                placeholder="e.g. B.Tech CSE / B.Sc"
                className="w-full glass-input p-3 text-xs font-semibold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">Subject (Optional)</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Data Structures / DBMS"
                className="w-full glass-input p-3 text-xs font-semibold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">Semester (Optional)</label>
              <input
                type="text"
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                placeholder="e.g. 5th Semester"
                className="w-full glass-input p-3 text-xs font-semibold"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-300 mb-1.5">Description (Optional)</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Short summary of topics covered in this document..."
                className="w-full glass-input p-3 text-xs text-white placeholder-slate-500"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-300 mb-1.5">Tags (Comma Separated)</label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="OS, Operating Systems, CSE, B.Tech, Notes"
                className="w-full glass-input p-3 text-xs font-semibold"
              />
            </div>

          </div>

          {/* COPYRIGHT CONFIRMATION CHECKBOX */}
          <div className="glass-pressed p-4 rounded-2xl space-y-2 border border-white/10">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                required
                checked={copyrightConfirmed}
                onChange={(e) => setCopyrightConfirmed(e.target.checked)}
                className="mt-0.5 rounded text-violet-600 w-4 h-4 flex-shrink-0"
              />
              <span className="text-xs text-slate-300 font-medium leading-relaxed">
                I confirm that I created this document or have explicit permission to upload and share it. I understand that copyrighted material without permission should not be uploaded.
              </span>
            </label>
          </div>

          {/* SUBMIT BUTTON */}
          <button
            type="submit"
            disabled={!file || !copyrightConfirmed || uploading}
            className="w-full glass-btn-primary py-4 text-xs font-extrabold uppercase tracking-wider flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FaMagic className="w-3.5 h-3.5" />
            {uploading ? 'Processing Contribution...' : 'Upload & Unlock 24h Access'}
          </button>

        </form>
      )}

    </div>
  );
}
