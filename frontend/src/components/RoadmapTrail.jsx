/**
 * RoadmapTrail — The signature UI element.
 *
 * Layout:
 *   • Desktop (≥640px): horizontal trail — nodes in a row, connector lines
 *     between them, expanded task panel below.
 *   • Mobile (<640px): vertical timeline — left-side circles, right-side
 *     module info, inline task expansion.
 *
 * Props:
 *   modules       — array of { title, tasks:[{task_id, title, is_completed}], resource_search_terms }
 *   interactive   — boolean: if true, tasks can be checked off (Dashboard use)
 *   onTaskToggle  — (taskId: string, isCompleted: boolean) => void
 *   initialIndex  — number: which module is open by default
 */
import React, { useState } from 'react';
import { Check, BookOpen, ExternalLink, ChevronDown, ChevronUp, Circle } from 'lucide-react';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getStatus(module) {
  const done = module.tasks.filter(t => t.is_completed).length;
  if (done === module.tasks.length) return 'completed';
  if (done > 0) return 'in-progress';
  return 'pending';
}

function progressPct(module) {
  const done = module.tasks.filter(t => t.is_completed).length;
  return Math.round((done / module.tasks.length) * 100);
}

// ─── Node circle ──────────────────────────────────────────────────────────────

function NodeCircle({ idx, status, isSelected, onClick }) {
  const base =
    'relative w-11 h-11 rounded-full flex items-center justify-center ' +
    'font-heading font-bold text-sm cursor-pointer transition-all duration-200 flex-shrink-0 select-none';

  const style = {
    completed:    'bg-green text-navy shadow-[0_0_0_3px_rgba(34,197,139,0.22)]',
    'in-progress': isSelected
      ? 'bg-signal text-white shadow-[0_0_0_4px_rgba(59,91,255,0.35)]'
      : 'bg-signal text-white shadow-[0_0_0_3px_rgba(59,91,255,0.2)]',
    pending:      'bg-[#1A2642] border-2 border-[#6B7280]/40 text-[#6B7280]',
  }[status];

  return (
    <button
      onClick={onClick}
      aria-label={`Module ${idx + 1}`}
      className={`${base} ${style} ${isSelected ? 'scale-110' : 'hover:scale-105'}`}
    >
      {status === 'completed' ? (
        <Check size={17} strokeWidth={3} />
      ) : (
        idx + 1
      )}
      {status === 'in-progress' && (
        <span className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full bg-amber border-2 border-[#0F1729] animate-pulse" />
      )}
    </button>
  );
}

// ─── Task Row ─────────────────────────────────────────────────────────────────

function TaskRow({ task, interactive, onToggle }) {
  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
        task.is_completed ? 'bg-[rgba(34,197,139,0.06)]' : 'bg-[#0F1729]/50 hover:bg-[#0F1729]/70'
      }`}
    >
      <button
        onClick={() => interactive && onToggle?.(task.task_id, !task.is_completed)}
        disabled={!interactive}
        aria-label={task.is_completed ? 'Mark incomplete' : 'Mark complete'}
        className={`w-5 h-5 rounded flex-shrink-0 mt-0.5 flex items-center justify-center border transition-all duration-150 ${
          task.is_completed
            ? 'bg-green border-green text-navy'
            : interactive
            ? 'border-[#6B7280]/40 hover:border-signal cursor-pointer'
            : 'border-[#6B7280]/30 cursor-default'
        }`}
      >
        {task.is_completed && <Check size={11} strokeWidth={3} />}
      </button>
      <span
        className={`text-sm leading-snug ${
          task.is_completed ? 'line-through text-slate' : 'text-offwhite'
        }`}
      >
        {task.title}
      </span>
    </div>
  );
}

// ─── Resource links ───────────────────────────────────────────────────────────

function ResourceLinks({ terms }) {
  if (!terms?.length) return null;
  return (
    <div className="mt-4 pt-4 border-t border-white/5">
      <p className="text-xs text-slate mb-2 flex items-center gap-1.5">
        <BookOpen size={11} /> Suggested resources
      </p>
      <div className="flex flex-wrap gap-2">
        {terms.map((term, i) => (
          <a
            key={i}
            href={`https://www.youtube.com/results?search_query=${encodeURIComponent(term)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] text-signal hover:underline"
          >
            <ExternalLink size={10} />
            {term}
          </a>
        ))}
      </div>
    </div>
  );
}

// ─── Task panel (shared between H and V views) ────────────────────────────────

function TaskPanel({ mod, interactive, onToggle }) {
  const done = mod.tasks.filter(t => t.is_completed).length;
  const pct  = progressPct(mod);

  return (
    <div className="card border border-white/5 mt-0">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-heading font-bold text-offwhite text-base">{mod.title}</h3>
          <p className="text-xs text-slate mt-0.5">{done}/{mod.tasks.length} tasks completed</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:block w-20 h-1.5 bg-navy rounded-full overflow-hidden">
            <div
              className="h-full bg-signal rounded-full transition-all duration-700"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs font-heading font-semibold text-signal">{pct}%</span>
        </div>
      </div>
      <div className="grid sm:grid-cols-2 gap-2">
        {mod.tasks.map(task => (
          <TaskRow key={task.task_id} task={task} interactive={interactive} onToggle={onToggle} />
        ))}
      </div>
      <ResourceLinks terms={mod.resource_search_terms} />
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function RoadmapTrail({
  modules,
  interactive = false,
  onTaskToggle,
  initialIndex = 0,
}) {
  const [selected, setSelected] = useState(initialIndex);

  const toggle = (i) => setSelected(prev => (prev === i ? null : i));
  const selectedMod = selected !== null ? modules[selected] : null;

  return (
    <div className="w-full">

      {/* ══════════════════════════════════════════════════
          MOBILE — Vertical Timeline  (hidden on sm+)
      ══════════════════════════════════════════════════ */}
      <div className="sm:hidden space-y-0">
        {modules.map((mod, i) => {
          const status  = getStatus(mod);
          const isSel   = selected === i;
          const done    = mod.tasks.filter(t => t.is_completed).length;
          const isLast  = i === modules.length - 1;

          return (
            <div key={i}>
              {/* Row: circle + connector | module info */}
              <div className="flex items-start gap-4">
                {/* Left spine */}
                <div className="flex flex-col items-center flex-shrink-0">
                  <NodeCircle idx={i} status={status} isSelected={isSel} onClick={() => toggle(i)} />
                  {!isLast && (
                    <div
                      className="w-0.5 mt-1"
                      style={{
                        height: isSel ? 0 : 36,
                        background: status === 'completed' ? 'rgba(34,197,139,0.35)' : 'rgba(107,114,128,0.2)',
                        transition: 'height 0.2s',
                      }}
                    />
                  )}
                </div>

                {/* Module info */}
                <button
                  onClick={() => toggle(i)}
                  className="flex-1 text-left py-2 min-w-0"
                >
                  <div className="flex items-center justify-between">
                    <p className={`font-heading font-semibold text-sm leading-snug pr-2 ${
                      status === 'completed' ? 'text-green' :
                      isSel || status === 'in-progress' ? 'text-offwhite' : 'text-slate'
                    }`}>
                      {mod.title}
                    </p>
                    {isSel
                      ? <ChevronUp size={14} className="text-slate flex-shrink-0" />
                      : <ChevronDown size={14} className="text-slate flex-shrink-0" />}
                  </div>
                  <p className="text-xs text-slate mt-0.5">{done}/{mod.tasks.length} tasks</p>
                </button>
              </div>

              {/* Inline task panel */}
              {isSel && (
                <div className="ml-14 mt-2 mb-4">
                  <TaskPanel mod={mod} interactive={interactive} onToggle={onTaskToggle} />
                </div>
              )}

              {/* Gap between items */}
              {!isSel && !isLast && <div className="h-2" />}
            </div>
          );
        })}
      </div>

      {/* ══════════════════════════════════════════════════
          DESKTOP — Horizontal Trail  (hidden below sm)
      ══════════════════════════════════════════════════ */}
      <div className="hidden sm:block">
        {/* Trail row: nodes + connectors */}
        <div className="flex items-start">
          {modules.map((mod, i) => {
            const status  = getStatus(mod);
            const isSel   = selected === i;
            const done    = mod.tasks.filter(t => t.is_completed).length;
            const isLast  = i === modules.length - 1;

            return (
              <React.Fragment key={i}>
                {/* Node column */}
                <div className="flex flex-col items-center flex-shrink-0" style={{ minWidth: 44 }}>
                  <NodeCircle idx={i} status={status} isSelected={isSel} onClick={() => toggle(i)} />
                  <button
                    onClick={() => toggle(i)}
                    className="mt-2.5 text-center w-28 group"
                  >
                    <p className={`font-heading font-semibold text-[11px] leading-snug transition-colors ${
                      status === 'completed' ? 'text-green' :
                      isSel ? 'text-signal' :
                      status === 'in-progress' ? 'text-offwhite' : 'text-slate group-hover:text-offwhite'
                    }`}>
                      {mod.title}
                    </p>
                    <p className="text-[10px] text-slate mt-0.5">{done}/{mod.tasks.length} tasks</p>
                  </button>
                </div>

                {/* Connector */}
                {!isLast && (
                  <div className="flex-1 flex items-start pt-[22px] min-w-[20px]">
                    <div
                      className="w-full h-0.5 rounded-full"
                      style={{
                        background: status === 'completed'
                          ? 'rgba(34,197,139,0.4)'
                          : 'rgba(107,114,128,0.2)',
                        backgroundImage: status === 'pending'
                          ? 'repeating-linear-gradient(90deg, rgba(107,114,128,0.25) 0 6px, transparent 6px 12px)'
                          : 'none',
                      }}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Expanded task panel */}
        {selectedMod && (
          <div className="mt-6 transition-all">
            <TaskPanel mod={selectedMod} interactive={interactive} onToggle={onTaskToggle} />
          </div>
        )}
      </div>
    </div>
  );
}
