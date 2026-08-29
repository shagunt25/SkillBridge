import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Plus, CheckCircle2, FileText, Keyboard } from 'lucide-react';
import Navbar from '../components/Navbar';
import { SUGGESTED_SKILLS } from '../data/mockData';
import { useAppContext, ACTIONS } from '../context/AppContext';

export default function OnboardingSkillsPage() {
  const navigate = useNavigate();
  const { dispatch } = useAppContext();
  
  const [mode, setMode] = useState('resume'); // 'resume' | 'manual'
  const [skills, setSkills] = useState([]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);

  const addSkill = (skill) => {
    const trimmed = skill.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills(prev => [...prev, trimmed]);
    }
  };

  const removeSkill = (skill) => setSkills(prev => prev.filter(s => s !== skill));

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill(input);
      setInput('');
    }
    if (e.key === 'Backspace' && !input && skills.length) {
      setSkills(prev => prev.slice(0, -1));
    }
  };

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/msword': ['.doc', '.docx'] },
    maxFiles: 1,
  });

  const canContinue = mode === 'manual' ? skills.length > 0 : file !== null;

  const handleContinue = () => {
    if (!canContinue) return;

    // Keep the File only for this browser session. It is never written to storage.
    // The backend integration must define how this file is uploaded/extracted.
    if (mode === 'manual') {
      dispatch({ type: ACTIONS.SET_SKILLS, payload: skills });
    } else {
      dispatch({ type: ACTIONS.SET_RESUME, payload: file });
    }
    navigate('/onboarding/target');
  };

  return (
    <div className="page-container">
      <Navbar />
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-12">
        {/* Step indicator */}
        <div className="flex items-center gap-3 mb-10">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-signal text-white text-xs font-heading font-bold flex items-center justify-center">1</div>
            <span className="text-sm font-medium text-offwhite">Your Skills</span>
          </div>
          <div className="flex-1 h-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-navy-light border border-white/10 text-slate text-xs font-heading font-bold flex items-center justify-center">2</div>
            <span className="text-sm text-slate">Your Target</span>
          </div>
        </div>

        <h1 className="font-heading font-bold text-3xl text-offwhite mb-2">What are your current skills?</h1>
        <p className="text-slate mb-8">Upload your resume for auto-detection, or type your skills manually.</p>

        {/* Mode toggle */}
        <div className="flex gap-1 p-1 bg-navy-light rounded-xl mb-8 border border-white/5">
          <button
            onClick={() => setMode('resume')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
              mode === 'resume'
                ? 'bg-signal text-white shadow-soft'
                : 'text-slate hover:text-offwhite'
            }`}
          >
            <FileText size={15} /> Upload Resume
          </button>
          <button
            onClick={() => setMode('manual')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
              mode === 'manual'
                ? 'bg-signal text-white shadow-soft'
                : 'text-slate hover:text-offwhite'
            }`}
          >
            <Keyboard size={15} /> Enter Manually
          </button>
        </div>

        {mode === 'resume' && (
          <div className="fade-up">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              id="resume-dropzone"
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors mb-6 ${
                isDragActive
                  ? 'border-signal bg-[rgba(59,91,255,0.06)]'
                  : file
                  ? 'border-green bg-[rgba(34,197,139,0.05)]'
                  : 'border-white/10 hover:border-white/20 hover:bg-white/[0.02]'
              }`}
            >
              <input {...getInputProps()} />
              {file ? (
                <div className="flex flex-col items-center gap-2">
                  <CheckCircle2 size={36} className="text-green" />
                  <p className="font-medium text-offwhite">{file.name}</p>
                  <p className="text-xs text-slate">{(file.size / 1024).toFixed(0)} KB · Click to change</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-14 h-14 rounded-full bg-navy-light border border-white/10 flex items-center justify-center">
                    <Upload size={24} className="text-slate" />
                  </div>
                  <div>
                    <p className="font-medium text-offwhite">
                      {isDragActive ? 'Drop it here…' : 'Drop your resume here'}
                    </p>
                    <p className="text-sm text-slate mt-1">PDF or Word · or <span className="text-signal">browse files</span></p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {mode === 'manual' && (
          <div className="fade-up">
            {/* Skill tag input */}
            <div className="card border border-white/5 mb-4">
              <label className="block text-sm font-medium text-offwhite mb-3" htmlFor="skill-input">
                Type a skill and press Enter
              </label>
              <div className={`flex flex-wrap gap-2 p-3 bg-navy rounded-lg border transition-colors min-h-[52px] ${
                input ? 'border-signal' : 'border-white/10'
              }`}>
                {skills.map(s => (
                  <span key={s} className="tag flex items-center gap-1.5">
                    {s}
                    <button onClick={() => removeSkill(s)} aria-label={`Remove ${s}`}
                      className="hover:text-red-400 transition-colors">
                      <X size={11} />
                    </button>
                  </span>
                ))}
                <input
                  id="skill-input"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={skills.length ? '' : 'e.g. Python, React, SQL…'}
                  className="flex-1 min-w-[140px] bg-transparent text-offwhite placeholder:text-slate text-sm outline-none"
                />
              </div>
              <p className="text-xs text-slate mt-2">Press Enter or comma to add each skill</p>
            </div>

            {/* Suggested skills */}
            <div className="mb-8">
              <p className="text-xs text-slate mb-3">Quick add:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_SKILLS.filter(s => !skills.includes(s)).slice(0, 10).map(s => (
                  <button
                    key={s}
                    onClick={() => addSkill(s)}
                    className="tag hover:border-signal hover:text-signal transition-colors flex items-center gap-1"
                  >
                    <Plus size={10} /> {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* CTA */}
        <button
          onClick={handleContinue}
          disabled={!canContinue}
          className={`btn-primary w-full mt-4 py-3.5 text-base justify-center ${
            !canContinue ? 'opacity-40 cursor-not-allowed' : ''
          }`}
        >
          Continue → Set Your Target
        </button>
        {!canContinue && (
          <p className="text-center text-xs text-slate mt-2">
            {mode === 'manual' ? 'Add at least one skill to continue' : 'Upload a resume to continue'}
          </p>
        )}
      </div>
    </div>
  );
}
