import React, { useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';

/**
 * CareerFlowNetwork
 * Minimalist, high-performance canvas & SVG animation.
 * Represents career progression through flowing topographic curves,
 * connected skill milestones, and subtle traveling light pulses.
 */
export default function CareerFlowNetwork({ isHovered = false, className = '' }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let width = (canvas.width = canvas.offsetWidth * window.devicePixelRatio || 600);
    let height = (canvas.height = canvas.offsetHeight * window.devicePixelRatio || 400);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth * window.devicePixelRatio || 600;
      height = canvas.height = canvas.offsetHeight * window.devicePixelRatio || 400;
    };

    window.addEventListener('resize', handleResize);

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Check if dark mode
    const isDark = document.documentElement.classList.contains('dark');

    // Subtle wave lines parameters
    const waves = [
      { yOffset: 0.3,  amplitude: 35, frequency: 0.002, speed: 0.0008, color: isDark ? 'rgba(45, 212, 191, 0.18)' : 'rgba(15, 118, 110, 0.14)' },
      { yOffset: 0.45, amplitude: 45, frequency: 0.0025, speed: 0.0012, color: isDark ? 'rgba(99, 201, 149, 0.22)' : 'rgba(25, 135, 84, 0.16)' },
      { yOffset: 0.62, amplitude: 40, frequency: 0.0018, speed: 0.0009, color: isDark ? 'rgba(228, 173, 88, 0.18)' : 'rgba(197, 138, 36, 0.14)' },
      { yOffset: 0.78, amplitude: 50, frequency: 0.0022, speed: 0.0015, color: isDark ? 'rgba(101, 199, 166, 0.15)' : 'rgba(13, 148, 136, 0.12)' },
    ];

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const speedMultiplier = isHovered ? 1.6 : 1.0;
      if (!prefersReducedMotion) {
        time += 1 * speedMultiplier;
      }

      // Draw flowing topographic waves
      waves.forEach((wave) => {
        ctx.beginPath();
        ctx.strokeStyle = wave.color;
        ctx.lineWidth = isHovered ? 2.5 : 1.75;

        const baseHeight = height * wave.yOffset;
        ctx.moveTo(0, baseHeight);

        for (let x = 0; x <= width; x += 12) {
          const y =
            baseHeight +
            Math.sin(x * wave.frequency + time * wave.speed) * wave.amplitude +
            Math.cos((x + time) * 0.001) * 12;
          ctx.lineTo(x, y);
        }
        ctx.stroke();
      });

      // Animated traveling light packets
      if (!prefersReducedMotion) {
        const packetX = ((time * 1.5) % width);
        const activeWave = waves[1];
        const packetY =
          height * activeWave.yOffset +
          Math.sin(packetX * activeWave.frequency + time * activeWave.speed) * activeWave.amplitude;

        // Glow
        const gradient = ctx.createRadialGradient(packetX, packetY, 0, packetX, packetY, 16);
        gradient.addColorStop(0, isDark ? 'rgba(101, 199, 166, 0.8)' : 'rgba(15, 118, 110, 0.8)');
        gradient.addColorStop(1, 'rgba(101, 199, 166, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(packetX, packetY, 16, 0, Math.PI * 2);
        ctx.fill();

        // Core dot
        ctx.fillStyle = isDark ? '#ffffff' : '#0f766e';
        ctx.beginPath();
        ctx.arc(packetX, packetY, 3, 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [isHovered]);

  return (
    <div className={`relative w-full h-full select-none pointer-events-none overflow-hidden ${className}`}>
      {/* Background canvas for flowing curves */}
      <canvas ref={canvasRef} className="w-full h-full absolute inset-0 block" />

      {/* Connected Skill Milestone Nodes */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="relative w-full max-w-lg h-72 mx-auto">
          {/* Milestone Node 1: Learn */}
          <div className="absolute left-[10%] top-[38%] flex flex-col items-center gap-1.5 transition-transform duration-300 hover:scale-110">
            <div className="w-7 h-7 rounded-full bg-surface border border-accent/40 shadow-sm flex items-center justify-center text-accent">
              <span className="w-2 h-2 rounded-full bg-accent animate-ping" />
            </div>
            <span className="text-[11px] font-medium text-text-secondary bg-surface/80 backdrop-blur-sm px-2 py-0.5 rounded-md border border-border">
              Learn
            </span>
          </div>

          {/* Milestone Node 2: Practice */}
          <div className="absolute left-[38%] top-[22%] flex flex-col items-center gap-1.5 transition-transform duration-300 hover:scale-110">
            <div className="w-8 h-8 rounded-full bg-surface border border-teal-500/50 shadow-sm flex items-center justify-center text-teal-600 dark:text-teal-300">
              <div className="w-2.5 h-2.5 rounded-full bg-teal-500" />
            </div>
            <span className="text-[11px] font-medium text-text-secondary bg-surface/80 backdrop-blur-sm px-2 py-0.5 rounded-md border border-border">
              Practice
            </span>
          </div>

          {/* Central Core Star Node: Apply */}
          <div className="absolute left-[64%] top-[42%] flex flex-col items-center gap-1.5 transition-transform duration-300 hover:scale-110">
            <div className="relative w-11 h-11 rounded-2xl bg-teal-700 dark:bg-emerald-500 text-white dark:text-zinc-950 flex items-center justify-center shadow-lg shadow-teal-700/20 dark:shadow-emerald-500/30 pulse-glow">
              <Sparkles size={18} />
            </div>
            <span className="text-[11px] font-semibold text-text-primary bg-surface/90 backdrop-blur-sm px-2.5 py-0.5 rounded-md border border-border shadow-sm">
              Apply
            </span>
          </div>

          {/* Milestone Node 4: Achieve */}
          <div className="absolute right-[8%] top-[60%] flex flex-col items-center gap-1.5 transition-transform duration-300 hover:scale-110">
            <div className="w-7 h-7 rounded-full bg-surface border border-amber-500/50 shadow-sm flex items-center justify-center text-amber-500">
              <div className="w-2 h-2 rounded-full bg-amber-500" />
            </div>
            <span className="text-[11px] font-medium text-text-secondary bg-surface/80 backdrop-blur-sm px-2 py-0.5 rounded-md border border-border">
              Achieve
            </span>
          </div>

          {/* Connecting SVG Spline */}
          <svg className="absolute inset-0 w-full h-full stroke-accent/25 fill-none stroke-[1.5] stroke-dasharray-[4,4] -z-10">
            <path d="M 60 120 Q 180 50, 310 135 T 460 190" />
          </svg>
        </div>
      </div>
    </div>
  );
}
