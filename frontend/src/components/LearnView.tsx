'use client';

import { useState, useEffect } from 'react';
import {
  Edit3,
  AlertCircle,
  CheckCircle,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  Brain,
  ArrowRight,
  Star,
  BarChart,
  X,
} from 'lucide-react';
import clsx from 'clsx';
import { submitFeedback } from '@/lib/api';
import type { FeedbackResult, Source } from '@/lib/types';

interface LearnViewProps {
  lastDraft: string;
  lastQuery: string;
  lastSources: Source[];
  onFeedbackSubmitted: () => void;
  onGoToAnalyze: () => void;
}

function StatCard({
  label,
  value,
  suffix = '%',
  description,
  colorClass,
}: {
  label: string;
  value: number;
  suffix?: string;
  description?: string;
  colorClass: string;
}) {
  return (
    <div className="bg-bg-primary border border-border rounded-xl p-4">
      <p className="text-xs text-text-muted uppercase tracking-wider font-medium mb-2">{label}</p>
      <p className={clsx('text-3xl font-bold', colorClass)}>
        {typeof value === 'number' ? value.toFixed(1) : value}
        <span className="text-lg">{suffix}</span>
      </p>
      {description && <p className="text-xs text-text-muted mt-1.5">{description}</p>}
    </div>
  );
}

function getScoreColor(score: number): string {
  if (score >= 75) return 'text-success-light';
  if (score >= 50) return 'text-accent-gold-light';
  return 'text-error-light';
}

function TrendIcon({ score }: { score: number }) {
  if (score >= 70) return <TrendingUp size={16} className="text-success-light" />;
  if (score >= 50) return <Minus size={16} className="text-accent-gold-light" />;
  return <TrendingDown size={16} className="text-error-light" />;
}

export default function LearnView({
  lastDraft,
  lastQuery,
  lastSources,
  onGoToAnalyze,
}: LearnViewProps) {
  const [editedDraft, setEditedDraft] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedbackResult, setFeedbackResult] = useState<FeedbackResult | null>(null);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  useEffect(() => {
    if (lastDraft) {
      setEditedDraft(lastDraft);
      setFeedbackResult(null);
      setError('');
    }
  }, [lastDraft]);

  const handleSubmit = async () => {
    if (!editedDraft.trim() || !lastDraft) return;
    setSubmitting(true);
    setError('');

    try {
      const docNames = lastSources.map((s) => s.file_name);
      const result = await submitFeedback(lastDraft, editedDraft, lastQuery, docNames);
      setFeedbackResult(result);
      setToast('Training complete! Preferences extracted and saved.');
      setTimeout(() => setToast(''), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Feedback submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  // No draft state
  if (!lastDraft) {
    return (
      <div className="p-6 max-w-5xl mx-auto animate-fade-in">
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-20 h-20 bg-bg-card border border-border rounded-2xl flex items-center justify-center mb-5">
            <Brain size={36} className="text-text-muted opacity-40" />
          </div>
          <h2 className="text-xl font-bold text-text-secondary mb-3">No Draft to Edit</h2>
          <p className="text-sm text-text-muted max-w-md mb-6">
            Generate a draft in the <strong className="text-text-secondary">Analyze</strong> tab
            first. Then come back here to refine it and train the system on your editing preferences.
          </p>
          <button
            onClick={onGoToAnalyze}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-primary-hover text-white font-medium text-sm rounded-lg transition-all duration-150 shadow-lg shadow-primary/20"
          >
            Go to Analyze
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-5 animate-fade-in">
      {/* Toast */}
      {toast && (
        <div className="fixed top-5 right-5 z-50 flex items-center gap-3 px-4 py-3 bg-success border border-success-light/30 text-white rounded-lg shadow-2xl shadow-success/30 animate-fade-in">
          <CheckCircle size={16} />
          <span className="text-sm font-medium">{toast}</span>
          <button onClick={() => setToast('')}>
            <X size={16} className="opacity-60 hover:opacity-100" />
          </button>
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Edit & Train</h1>
        <p className="text-sm text-text-secondary mt-1">
          Refine the generated draft. Your edits train the system to match your preferred style.
        </p>
      </div>

      {/* Query context */}
      {lastQuery && (
        <div className="flex items-center gap-3 px-4 py-2.5 bg-bg-card border border-border rounded-lg">
          <Edit3 size={14} className="text-accent-gold flex-shrink-0" />
          <div className="text-sm">
            <span className="text-text-muted">Query: </span>
            <span className="text-text-secondary font-medium">{lastQuery}</span>
          </div>
        </div>
      )}

      {/* Two-column editor */}
      <div className="grid grid-cols-2 gap-5">
        {/* Original draft (read-only) */}
        <div className="bg-bg-card border border-border rounded-xl overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
            <div className="w-2.5 h-2.5 rounded-full bg-text-muted" />
            <span className="text-sm font-semibold text-text-secondary">Original Draft</span>
            <span className="ml-auto text-xs text-text-muted">Read-only</span>
          </div>
          <div className="p-4 overflow-y-auto max-h-[60vh]">
            <pre className="text-xs text-text-secondary whitespace-pre-wrap leading-relaxed font-mono">
              {lastDraft}
            </pre>
          </div>
        </div>

        {/* Editable draft */}
        <div className="bg-bg-card border border-border rounded-xl overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
            <div className="w-2.5 h-2.5 rounded-full bg-primary" />
            <span className="text-sm font-semibold text-text-primary">Your Edit</span>
            <span className="ml-auto text-xs text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
              Editable
            </span>
          </div>
          <textarea
            value={editedDraft}
            onChange={(e) => setEditedDraft(e.target.value)}
            className="w-full h-[60vh] bg-transparent px-4 py-4 text-xs text-text-primary leading-relaxed font-mono focus:outline-none resize-none"
            placeholder="Edit the draft here..."
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-error/10 border border-error/30 rounded-lg text-error-light text-sm">
          <AlertCircle size={16} className="flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError('')} className="ml-auto">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={submitting || !editedDraft.trim() || editedDraft === lastDraft}
        className={clsx(
          'w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-sm transition-all duration-150',
          submitting || !editedDraft.trim() || editedDraft === lastDraft
            ? 'bg-primary/30 text-white/40 cursor-not-allowed'
            : 'bg-primary hover:bg-primary-hover text-white shadow-lg shadow-primary/20'
        )}
      >
        {submitting ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Analyzing edits and extracting preferences...
          </>
        ) : (
          <>
            <Brain size={16} />
            Submit Edits & Train
          </>
        )}
      </button>

      {editedDraft === lastDraft && !feedbackResult && (
        <p className="text-xs text-text-muted text-center">
          Make edits to the draft on the right to enable training
        </p>
      )}

      {/* Feedback results */}
      {feedbackResult && (
        <div className="space-y-5 animate-fade-in">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <BarChart size={16} className="text-primary" />
            <h2 className="text-base font-bold text-text-primary">Training Results</h2>
            <CheckCircle size={14} className="text-success-light ml-1" />
          </div>

          {/* Metrics cards */}
          <div className="grid grid-cols-4 gap-4">
            <StatCard
              label="Improvement Score"
              value={feedbackResult.edit_metrics.improvement_score}
              description={
                feedbackResult.edit_metrics.improvement_score >= 75
                  ? 'Significant improvement'
                  : feedbackResult.edit_metrics.improvement_score >= 50
                  ? 'Moderate improvement'
                  : 'Minor changes detected'
              }
              colorClass={getScoreColor(feedbackResult.edit_metrics.improvement_score)}
            />
            <StatCard
              label="Content Retained"
              value={feedbackResult.edit_metrics.retained_pct}
              description="Percentage of original preserved"
              colorClass="text-primary-hover"
            />
            <StatCard
              label="Edit Distance"
              value={feedbackResult.edit_metrics.edit_distance_pct}
              description="Normalized change magnitude"
              colorClass="text-accent-gold-light"
            />
            <StatCard
              label="New Content"
              value={feedbackResult.edit_metrics.additions_pct}
              description="Percentage of additions"
              colorClass="text-text-secondary"
            />
          </div>

          {/* Trend indicator */}
          <div className="flex items-center gap-3 px-4 py-3 bg-bg-card border border-border rounded-lg">
            <TrendIcon score={feedbackResult.edit_metrics.improvement_score} />
            <span className="text-sm text-text-secondary">
              {feedbackResult.edit_metrics.improvement_score >= 75
                ? 'Excellent edit quality — the system learned high-value preferences from your changes.'
                : feedbackResult.edit_metrics.improvement_score >= 50
                ? 'Good edit quality — meaningful preferences were extracted from your revisions.'
                : 'Minor edit — some preferences captured. Larger revisions yield richer training signals.'}
            </span>
          </div>

          {/* Extracted preferences */}
          {feedbackResult.preferences_extracted.length > 0 && (
            <div className="bg-bg-card border border-border rounded-xl overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-3 border-b border-border">
                <Star size={14} className="text-accent-gold" />
                <span className="text-sm font-semibold text-text-primary">
                  Learned Preferences
                </span>
                <span className="ml-auto text-xs text-text-muted bg-bg-primary px-2 py-0.5 rounded">
                  {feedbackResult.preferences_extracted.length} extracted
                </span>
              </div>
              <div className="p-4 space-y-2">
                {feedbackResult.preferences_extracted.map((pref, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 bg-bg-primary border border-subtle rounded-lg"
                  >
                    <div className="flex-shrink-0 w-5 h-5 bg-success/10 border border-success/30 rounded flex items-center justify-center text-xs font-bold text-success-light">
                      {i + 1}
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">{pref}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Message */}
          {feedbackResult.message && (
            <div className="flex items-start gap-3 p-4 bg-primary/5 border border-primary/20 rounded-lg">
              <Brain size={16} className="text-primary flex-shrink-0 mt-0.5" />
              <p className="text-sm text-text-secondary">{feedbackResult.message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
