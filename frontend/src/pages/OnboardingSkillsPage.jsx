import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, X, Plus, FileText, CheckCircle2, ArrowRight } from 'lucide-react';
import WorkflowLayout from '../components/WorkflowLayout';
import { useAppContext, ACTIONS } from '../context/AppContext';

// Default skills if none are populated
const INITIAL_EXTRACTED_SKILLS = [
  'Python',
  'Git',
  'REST APIs',
  'Pandas',
  'PostgreSQL',
  'Linux',
  'Data Analysis',
];

export default function OnboardingSkillsPage() {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();

  const [skills, setSkills] = useState(() => {
    return state.currentSkills && state.currentSkills.length > 0
      ? state.currentSkills
      : INITIAL_EXTRACTED_SKILLS;
  });
  const [file, setFile] = useState(state.resumeFile || null);
  const [isAdding, setIsAdding] = useState(false);
  const [newSkill, setNewSkill] = useState('');

  // Keep global state synced
  useEffect(() => {
    if (skills.length > 0) {
      dispatch({ type: ACTIONS.SET_SKILLS, payload: skills });
    }
  }, [skills, dispatch]);

  const addSkill = (name) => {
    const trimmed = name.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills((prev) => [...prev, trimmed]);
    }
    setNewSkill('');
    setIsAdding(false);
  };

  const removeSkill = (skillToRemove) => {
    setSkills((prev) => prev.filter((s) => s !== skillToRemove));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill(newSkill);
    } else if (e.key === 'Escape') {
      setIsAdding(false);
      setNewSkill('');
    }
  };

  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles && acceptedFiles.length > 0) {
        const uploaded = acceptedFiles[0];
        setFile(uploaded);
        dispatch({ type: ACTIONS.SET_RESUME, payload: uploaded });
      }
    },
    [dispatch]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  const handleContinue = () => {
    dispatch({ type: ACTIONS.SET_SKILLS, payload: skills });
    navigate('/onboarding/target');
  };

  return (
    <WorkflowLayout currentStep={2} pageTitle="Upload resume">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-left space-y-1.5">
          <p className="text-xs font-semibold uppercase tracking-wider text-accent">
            Step 1 of 4
          </p>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Tell us about your background
          </h1>
          <p className="text-sm text-text-secondary">
            Upload your resume for automated skill extraction, or refine your verified skills below.
          </p>
        </div>

        {/* ── Dropzone Area ── */}
        <div
          {...getRootProps()}
          className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center cursor-pointer transition-all duration-200 select-none ${
            isDragActive
              ? 'border-accent bg-accent/10 scale-[1.01]'
              : file
              ? 'border-emerald-500/40 bg-emerald-500/5'
              : 'border-border hover:border-accent/60 bg-surface'
          }`}
        >
          <input {...getInputProps()} />

          <div className="flex flex-col items-center gap-3">
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-colors ${
                file
                  ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                  : 'bg-accent/10 text-accent'
              }`}
            >
              {file ? <CheckCircle2 size={24} /> : <UploadCloud size={24} />}
            </div>

            {file ? (
              <div>
                <p className="text-sm font-semibold text-text-primary flex items-center justify-center gap-2">
                  <FileText size={15} />
                  <span>{file.name}</span>
                </p>
                <p className="text-xs text-text-secondary mt-1">
                  {(file.size / 1024).toFixed(1)} KB — Ready for analysis
                </p>
                <p className="text-xs text-accent font-medium mt-2">
                  Click or drag another file to replace
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  {isDragActive ? 'Drop your resume here…' : 'Drag & drop your resume'}
                </p>
                <p className="text-xs text-text-secondary mt-1">
                  Supported formats: PDF, DOCX, TXT (up to 10MB)
                </p>
                <span className="inline-block mt-3 text-xs font-medium text-accent bg-surface-muted px-3 py-1.5 rounded-lg border border-border">
                  Browse files
                </span>
              </div>
            )}
          </div>
        </div>

        {/* ── Extracted Skills Section ── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Extracted skills ({skills.length})
            </h2>
            <span className="text-xs text-text-secondary/80">
              Click a tag to remove
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {skills.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-muted border border-border text-text-primary group hover:border-accent/40 transition-colors"
              >
                <span>{skill}</span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeSkill(skill);
                  }}
                  aria-label={`Remove ${skill}`}
                  className="text-text-secondary hover:text-danger ml-0.5 rounded-full p-0.5"
                >
                  <X size={13} />
                </button>
              </span>
            ))}

            {isAdding ? (
              <div className="inline-flex items-center gap-1">
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Skill name + Enter"
                  autoFocus
                  className="text-xs bg-surface border border-accent rounded-xl px-3 py-1.5 text-text-primary focus:outline-none w-36"
                />
                <button
                  type="button"
                  onClick={() => addSkill(newSkill)}
                  className="p-1.5 rounded-lg bg-accent text-white dark:text-zinc-950 text-xs"
                >
                  <Plus size={13} />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsAdding(false);
                    setNewSkill('');
                  }}
                  className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary text-xs"
                >
                  <X size={13} />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsAdding(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border border-dashed border-border hover:border-accent text-text-secondary hover:text-accent transition-colors"
              >
                <Plus size={13} />
                <span>Add skill</span>
              </button>
            )}
          </div>
        </div>

        {/* ── Continue Action ── */}
        <div className="pt-6 border-t border-border flex justify-end">
          <button
            type="button"
            onClick={handleContinue}
            disabled={skills.length === 0 && !file}
            className="btn-accent px-6 py-2.5 flex items-center gap-2 text-sm font-semibold"
          >
            <span>Continue to Target Role</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </WorkflowLayout>
  );
}
