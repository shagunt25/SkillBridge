import React, { useEffect, useRef } from 'react';

/**
 * AuthBackgroundMotion
 * Subtle, calm animated background for Login and Signup pages.
 * Renders slow flowing contour ribbons and connected ambient skill constellation nodes.
 * Theme-aware (light/dark) and respects prefers-reduced-motion.
 */
export default function AuthBackgroundMotion({ className = '' }) {
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

    const handleResize = () => {
      if (!canvas) return;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.parentElement ? canvas.parentElement.offsetWidth : window.innerWidth;
      height = canvas.parentElement ? canvas.parentElement.offsetHeight : window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    let prefersReducedMotion = mediaQuery.matches;
    const handleMotionChange = (e) => {
      prefersReducedMotion = e.matches;
    };
    mediaQuery.addEventListener('change', handleMotionChange);

    const checkIsDark = () => document.documentElement.classList.contains('dark');

    // Ambient constellation nodes
    const nodeCount = 18;
    const nodes = Array.from({ length: nodeCount }, () => ({
      x: Math.random() * (width || 600),
      y: Math.random() * (height || 800),
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      radius: Math.random() * 2 + 1.2,
      alpha: Math.random() * 0.4 + 0.2,
    }));

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      const isDark = checkIsDark();

      if (!prefersReducedMotion) {
        time += 0.5;
      }

      // Draw gentle undulating contour curves
      const curves = [
        { yBase: 0.35, amp: 30, freq: 0.002, speed: 0.0004, color: isDark ? 'rgba(101, 199, 166, 0.12)' : 'rgba(15, 118, 110, 0.08)' },
        { yBase: 0.55, amp: 40, freq: 0.0015, speed: 0.0005, color: isDark ? 'rgba(45, 212, 191, 0.14)' : 'rgba(13, 148, 136, 0.09)' },
        { yBase: 0.75, amp: 35, freq: 0.0022, speed: 0.0003, color: isDark ? 'rgba(99, 201, 149, 0.10)' : 'rgba(25, 135, 84, 0.07)' },
      ];

      curves.forEach((c) => {
        ctx.beginPath();
        ctx.strokeStyle = c.color;
        ctx.lineWidth = 1.5;

        const baseY = height * c.yBase;
        const step = 20;
        let started = false;

        for (let x = 0; x <= width + step; x += step) {
          const y =
            baseY +
            Math.sin(x * c.freq + time * c.speed) * c.amp +
            Math.cos(x * 0.001 - time * (c.speed * 0.7)) * 12;

          if (!started) {
            ctx.moveTo(x, y);
            started = true;
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      });

      // Update and draw constellation nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (!prefersReducedMotion) {
          n.x += n.vx;
          n.y += n.vy;

          if (n.x < -10) n.x = width + 10;
          if (n.x > width + 10) n.x = -10;
          if (n.y < -10) n.y = height + 10;
          if (n.y > height + 10) n.y = -10;
        }

        // Draw connections between nearby nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          const dist = Math.hypot(n.x - n2.x, n.y - n2.y);
          if (dist < 130) {
            const edgeAlpha = (1 - dist / 130) * 0.15;
            ctx.beginPath();
            ctx.strokeStyle = isDark
              ? `rgba(101, 199, 166, ${edgeAlpha})`
              : `rgba(15, 118, 110, ${edgeAlpha})`;
            ctx.lineWidth = 1;
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.stroke();
          }
        }

        // Draw node
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = isDark
          ? `rgba(101, 199, 166, ${n.alpha * 0.7})`
          : `rgba(15, 118, 110, ${n.alpha * 0.5})`;
        ctx.fill();
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      mediaQuery.removeEventListener('change', handleMotionChange);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className={`absolute inset-0 pointer-events-none overflow-hidden ${className}`}
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}
