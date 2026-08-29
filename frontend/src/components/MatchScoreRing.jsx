import { useEffect, useState } from 'react';

/**
 * Animated SVG circular progress ring for the match score.
 * Colour transitions: ≥70 = green, ≥40 = amber, <40 = signal blue.
 */
export default function MatchScoreRing({ score, size = 130 }) {
  const [animated, setAnimated] = useState(0);
  const strokeWidth = 9;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animated / 100) * circumference;

  useEffect(() => {
    const t = setTimeout(() => setAnimated(score), 120);
    return () => clearTimeout(t);
  }, [score]);

  const color =
    score >= 70 ? '#22C58B' :
    score >= 40 ? '#FFB648' : '#3B5BFF';

  const label =
    score >= 70 ? 'Great Match' :
    score >= 40 ? 'Fair Match'  : 'Low Match';

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" style={{ flexShrink: 0 }}>
        {/* Track */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="#1A2642" strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.1s cubic-bezier(0.4,0,0.2,1), stroke 0.3s' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-heading font-bold text-2xl text-offwhite leading-none">{score}%</span>
        <span className="text-[11px] text-slate mt-0.5">{label}</span>
      </div>
    </div>
  );
}
