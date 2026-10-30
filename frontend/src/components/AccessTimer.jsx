import React, { useState, useEffect } from 'react';
import { FaClock, FaUnlock, FaLock } from 'react-icons/fa';

export default function AccessTimer({ remainingSeconds: initialSeconds, onExpire }) {
  const [seconds, setSeconds] = useState(initialSeconds || 0);

  useEffect(() => {
    setSeconds(initialSeconds || 0);
  }, [initialSeconds]);

  useEffect(() => {
    if (seconds <= 0) return;
    const interval = setInterval(() => {
      setSeconds(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          if (onExpire) onExpire();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [seconds, onExpire]);

  if (seconds <= 0) {
    return (
      <div className="glass-card p-5 border-l-4 border-amber-500 bg-amber-500/10">
        <div className="flex items-start gap-3">
          <div className="p-2.5 glass-pressed rounded-xl text-amber-400">
            <FaLock className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-white text-sm">Download Access Expired</h4>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              Upload a valid study document to unlock another 24 hours of unlimited library downloads.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return (
    <div className="glass-card p-5 border-l-4 border-emerald-500 bg-emerald-500/10 relative overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        
        <div className="flex items-center gap-3.5">
          <div className="p-3 glass-pressed rounded-2xl text-emerald-400 animate-pulse">
            <FaUnlock className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="glass-chip px-2.5 py-0.5 text-[10px] text-emerald-300 bg-emerald-500/20 uppercase tracking-wider font-bold">
                ✓ Active Contributor
              </span>
              <span className="text-xs font-extrabold text-emerald-400">Unlimited Downloads</span>
            </div>
            <p className="text-xs text-slate-300 mt-1 font-medium">Access expires in:</p>
          </div>
        </div>

        {/* COUNTDOWN DIGITS */}
        <div className="flex items-center gap-2 font-mono text-white font-black self-end sm:self-auto">
          <div className="glass-pressed px-3 py-2 rounded-xl text-base text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
            {String(hours).padStart(2, '0')}h
          </div>
          <span className="text-emerald-400/60 font-bold">:</span>
          <div className="glass-pressed px-3 py-2 rounded-xl text-base text-emerald-400 border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
            {String(mins).padStart(2, '0')}m
          </div>
          <span className="text-emerald-400/60 font-bold">:</span>
          <div className="glass-pressed px-3 py-2 rounded-xl text-base text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-500/10">
            {String(secs).padStart(2, '0')}s
          </div>
        </div>

      </div>
    </div>
  );
}
