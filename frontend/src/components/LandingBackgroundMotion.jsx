import React, { useEffect, useRef } from 'react';

/**
 * LandingBackgroundMotion
 * High-performance, elegant HTML5 canvas animation for SkillBridge AI landing page.
 * Renders continuous, organic flowing topographic curves and floating ambient particles
 * in the SkillBridge green/teal visual identity.
 * Features subtle, smooth cursor attraction/wave responsiveness and respects reduced-motion.
 */
export default function LandingBackgroundMotion({ className = '' }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId;
    let width = 0;
    let height = 0;
    let dpr = 1;

    // Mouse tracking with smooth lerp
    let mouse = { x: -1000, y: -1000, targetX: -1000, targetY: -1000, active: false };

    const handleMouseMove = (e) => {
      mouse.targetX = e.clientX;
      mouse.targetY = e.clientY;
      mouse.active = true;
    };

    const handleMouseLeave = () => {
      mouse.active = false;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    // Resize handling with DPR limit to avoid excessive pixel calculations
    const handleResize = () => {
      if (!canvas) return;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // Reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    let prefersReducedMotion = mediaQuery.matches;
    const handleMotionChange = (e) => {
      prefersReducedMotion = e.matches;
    };
    mediaQuery.addEventListener('change', handleMotionChange);

    // Check if dark mode is active on html root
    const checkIsDark = () => document.documentElement.classList.contains('dark');

    // Ambient floating particles
    const particleCount = 28;
    const particles = Array.from({ length: particleCount }, () => ({
      x: Math.random() * (width || window.innerWidth),
      y: Math.random() * (height || window.innerHeight),
      radius: Math.random() * 2 + 1,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25 - 0.15,
      alpha: Math.random() * 0.5 + 0.2,
      pulseSpeed: Math.random() * 0.02 + 0.01,
      pulsePhase: Math.random() * Math.PI * 2,
    }));

    // Wave parameters - refined organic frequencies and phase offsets
    const waveDefs = [
      { yRatio: 0.28, amp: 45, freq: 0.0016, speed: 0.0006, colorDark: 'rgba(101, 199, 166, 0.11)', colorLight: 'rgba(15, 118, 110, 0.08)' },
      { yRatio: 0.44, amp: 60, freq: 0.0012, speed: 0.0008, colorDark: 'rgba(45, 212, 191, 0.13)', colorLight: 'rgba(13, 148, 136, 0.09)' },
      { yRatio: 0.62, amp: 50, freq: 0.0018, speed: 0.0005, colorDark: 'rgba(99, 201, 149, 0.10)', colorLight: 'rgba(25, 135, 84, 0.07)' },
      { yRatio: 0.80, amp: 55, freq: 0.0014, speed: 0.0007, colorDark: 'rgba(101, 199, 166, 0.08)', colorLight: 'rgba(15, 118, 110, 0.06)' },
    ];

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      const isDark = checkIsDark();

      // Smooth mouse lerp
      if (mouse.active) {
        mouse.x += (mouse.targetX - mouse.x) * 0.05;
        mouse.y += (mouse.targetY - mouse.y) * 0.05;
      }

      if (!prefersReducedMotion) {
        time += 1;
      }

      // Draw flowing ribbons / wave curves
      waveDefs.forEach((w) => {
        ctx.beginPath();
        ctx.strokeStyle = isDark ? w.colorDark : w.colorLight;
        ctx.lineWidth = 1.75;

        const baseY = height * w.yRatio;
        const step = 16;
        let started = false;

        for (let x = 0; x <= width + step; x += step) {
          // Dynamic organic wave offset with dual sine harmony
          let waveOffset =
            Math.sin(x * w.freq + time * w.speed) * w.amp +
            Math.cos(x * (w.freq * 0.7) - time * (w.speed * 0.6)) * (w.amp * 0.4);

          // Subtle cursor repulsion / elevation
          if (mouse.active) {
            const dx = x - mouse.x;
            const dist = Math.abs(dx);
            if (dist < 220) {
              const influence = Math.cos((dist / 220) * (Math.PI / 2));
              const dyMouse = (mouse.y - baseY) * 0.12;
              waveOffset += influence * dyMouse;
            }
          }

          const currentY = baseY + waveOffset;

          if (!started) {
            ctx.moveTo(x, currentY);
            started = true;
          } else {
            ctx.lineTo(x, currentY);
          }
        }
        ctx.stroke();
      });

      // Draw subtle ambient particles
      particles.forEach((p) => {
        if (!prefersReducedMotion) {
          p.x += p.vx;
          p.y += p.vy;

          if (p.x < -10) p.x = width + 10;
          if (p.x > width + 10) p.x = -10;
          if (p.y < -10) p.y = height + 10;
          if (p.y > height + 10) p.y = -10;
        }

        // Particle pulse
        const pulse = 0.6 + Math.sin(time * p.pulseSpeed + p.pulsePhase) * 0.4;
        const currentAlpha = p.alpha * pulse;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = isDark
          ? `rgba(101, 199, 166, ${currentAlpha * 0.7})`
          : `rgba(15, 118, 110, ${currentAlpha * 0.5})`;
        ctx.fill();
      });

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      mediaQuery.removeEventListener('change', handleMotionChange);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className={`fixed inset-0 pointer-events-none -z-10 overflow-hidden ${className}`}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
        style={{ opacity: 0.95 }}
      />
    </div>
  );
}
