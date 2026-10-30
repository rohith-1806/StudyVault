import React, { useEffect, useRef, useState } from 'react';
import { useTheme } from '../context/ThemeContext';

export default function CustomCursor() {
  const { isDark } = useTheme();
  const dotRef = useRef(null);
  const ringRef = useRef(null);
  const rippleRef = useRef(null);

  const [isVisible, setIsVisible] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isInput, setIsInput] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const [isTouchOrSmall, setIsTouchOrSmall] = useState(false);

  useEffect(() => {
    // Check if device is touch, small screen, or reduced motion
    const checkTouchOrReducedMotion = () => {
      const isTouch = window.matchMedia('(pointer: coarse)').matches || 
                      'ontouchstart' in window || 
                      window.innerWidth < 768;
      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const disabled = isTouch || prefersReduced;
      setIsTouchOrSmall(disabled);

      if (disabled) {
        document.documentElement.classList.remove('has-custom-cursor');
        document.body.classList.remove('has-custom-cursor');
      } else {
        document.documentElement.classList.add('has-custom-cursor');
        document.body.classList.add('has-custom-cursor');
      }
    };

    checkTouchOrReducedMotion();
    window.addEventListener('resize', checkTouchOrReducedMotion);

    return () => {
      window.removeEventListener('resize', checkTouchOrReducedMotion);
      document.documentElement.classList.remove('has-custom-cursor');
      document.body.classList.remove('has-custom-cursor');
    };
  }, []);

  useEffect(() => {
    if (isTouchOrSmall) {
      document.documentElement.classList.remove('has-custom-cursor');
      document.body.classList.remove('has-custom-cursor');
      return;
    }

    // Apply global class to hide native cursor on desktop
    document.documentElement.classList.add('has-custom-cursor');
    document.body.classList.add('has-custom-cursor');

    let rafId;
    // Position targets and current lerp positions
    const target = { x: -100, y: -100 };
    const dot = { x: -100, y: -100 };
    const ring = { x: -100, y: -100 };

    const handleMouseMove = (e) => {
      target.x = e.clientX;
      target.y = e.clientY;

      if (!isVisible) setIsVisible(true);

      // Check hovered element
      const targetEl = e.target;
      if (targetEl && targetEl.closest) {
        const isInteractive = Boolean(
          targetEl.closest('button, a, [role="button"], .glass-card-hover, .interactive-hover, .glass-btn, .glass-btn-primary, .cursor-pointer')
        );
        const isInputField = Boolean(
          targetEl.closest('input, textarea, select, [contenteditable="true"]')
        );

        setIsHovered(isInteractive);
        setIsInput(isInputField);
      }
    };

    const handleMouseDown = () => {
      setIsClicking(true);
      if (rippleRef.current) {
        rippleRef.current.style.transform = `translate3d(${target.x}px, ${target.y}px, 0) scale(1.6)`;
        rippleRef.current.style.opacity = '0';
        rippleRef.current.style.transition = 'transform 0.4s ease-out, opacity 0.4s ease-out';
      }
    };

    const handleMouseUp = () => {
      setIsClicking(false);
      if (rippleRef.current) {
        setTimeout(() => {
          if (rippleRef.current) {
            rippleRef.current.style.transition = 'none';
            rippleRef.current.style.transform = `translate3d(${target.x}px, ${target.y}px, 0) scale(0.4)`;
            rippleRef.current.style.opacity = '0.5';
          }
        }, 300);
      }
    };

    const handleMouseLeave = () => {
      setIsVisible(false);
    };

    const handleMouseEnter = () => {
      setIsVisible(true);
    };

    // Smooth animation loop using requestAnimationFrame and lerp
    const render = () => {
      // Direct fast follow for center dot
      dot.x += (target.x - dot.x) * 0.75;
      dot.y += (target.y - dot.y) * 0.75;

      // Smooth lag / trailing for outer ring
      ring.x += (target.x - ring.x) * 0.18;
      ring.y += (target.y - ring.y) * 0.18;

      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${dot.x}px, ${dot.y}px, 0)`;
      }

      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${ring.x}px, ${ring.y}px, 0)`;
      }

      rafId = requestAnimationFrame(render);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);

    rafId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
      if (rafId) cancelAnimationFrame(rafId);
      document.documentElement.classList.remove('has-custom-cursor');
      document.body.classList.remove('has-custom-cursor');
    };
  }, [isTouchOrSmall, isVisible]);

  if (isTouchOrSmall) return null;

  // Compute ring styling classes based on interaction state
  let ringClasses = 'w-9 h-9 border rounded-full transition-all duration-200 ease-out flex items-center justify-center pointer-events-none';
  let dotClasses = 'w-2 h-2 rounded-full transition-all duration-150 ease-out pointer-events-none';

  if (isDark) {
    dotClasses += ' bg-gradient-to-r from-violet-400 via-indigo-400 to-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.6)]';
    if (isInput) {
      // Over input fields, keep native text I-beam primary and reduce custom cursor to faint indicator
      ringClasses += ' w-6 h-6 border-violet-400/30 scale-75 opacity-15';
      dotClasses += ' opacity-0 scale-50';
    } else if (isHovered) {
      ringClasses += ' w-13 h-13 border-cyan-400/80 bg-violet-600/15 shadow-[0_0_18px_rgba(139,92,246,0.45)] scale-125';
      dotClasses += ' scale-125';
    } else {
      ringClasses += ' border-violet-400/40 bg-violet-500/5';
    }
  } else {
    // Light Theme cursor: vibrant indigo/cyan with crisp contrast
    dotClasses += ' bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-600 shadow-[0_0_6px_rgba(99,102,241,0.5)]';
    if (isInput) {
      ringClasses += ' w-6 h-6 border-indigo-600/30 scale-75 opacity-15';
      dotClasses += ' opacity-0 scale-50';
    } else if (isHovered) {
      ringClasses += ' w-13 h-13 border-violet-600/80 bg-violet-500/20 shadow-[0_0_15px_rgba(124,58,237,0.35)] scale-125';
      dotClasses += ' scale-125';
    } else {
      ringClasses += ' border-violet-500/40 bg-violet-500/10';
    }
  }

  if (isClicking && !isInput) {
    ringClasses += ' scale-90 opacity-90';
    dotClasses += ' scale-75';
  }

  return (
    <div
      className={`fixed inset-0 pointer-events-none z-[99999] transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      aria-hidden="true"
    >
      {/* OUTER LERPING RING */}
      <div
        ref={ringRef}
        className="fixed top-0 left-0 pointer-events-none will-change-transform -translate-x-1/2 -translate-y-1/2"
        style={{ transform: 'translate3d(-100px, -100px, 0)' }}
      >
        <div className={ringClasses} />
      </div>

      {/* CENTER GLOWING DOT */}
      <div
        ref={dotRef}
        className="fixed top-0 left-0 pointer-events-none will-change-transform -translate-x-1/2 -translate-y-1/2"
        style={{ transform: 'translate3d(-100px, -100px, 0)' }}
      >
        <div className={dotClasses} />
      </div>

      {/* CLICK RIPPLE ELEMENT */}
      <div
        ref={rippleRef}
        className={`fixed top-0 left-0 w-10 h-10 rounded-full pointer-events-none -translate-x-1/2 -translate-y-1/2 border ${
          isDark ? 'border-cyan-400/60' : 'border-violet-600/60'
        } opacity-0`}
        style={{ transform: 'translate3d(-100px, -100px, 0) scale(0.4)' }}
      />
    </div>
  );
}
