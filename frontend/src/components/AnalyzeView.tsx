'use client';

import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Search,
  FileText,
  Loader2,
  Copy,
  Download,
  CheckCheck,
  AlertCircle,
  Sparkles,
  BookOpen,
  SlidersHorizontal,
  X,
  ExternalLink,
} from 'lucide-react';
import clsx from 'clsx';
import { generateDraft } from '@/lib/api';
import type { DraftResult, Source } from '@/lib/types';

interface AnalyzeViewProps {
  selectedDocId: string | null;
  selectedDocName: string;
  onDraftGenerated: (result: DraftResult, query: string) => void;
}

function RelevanceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? 'bg-success-light' : pct >= 60 ? 'bg-accent-gold-light' : 'bg-error-light';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-bg-primary rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-text-muted w-8 text-right">{pct}%</span>
    </div>
  );
}

function SourceCard({ source }: { source: Source }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="bg-bg-primary border border-border rounded-lg overflow-hidden hover:border-border/80 transition-colors">
      <div className="p-3">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="flex-shrink-0 w-5 h-5 bg-primary/20 border border-primary/30 rounded text-xs font-bold text-primary flex items-center justify-center">
              {source.source_number}
            </span>
            <span className="text-xs font-medium text-text-primary truncate">
              {source.file_name}
            </span>
          </div>
        </div>
        <RelevanceBar score={source.relevance_score} />
        <div className="mt-2">
          <p
            className={clsx(
              'text-xs text-text-secondary leading-relaxed',
              !expanded && 'line-clamp-3'
            )}
          >
            {source.excerpt}
          </p>
          {source.excerpt && source.excerpt.length > 150 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-primary hover:text-primary-hover mt-1 flex items-center gap-1"
            >
              <ExternalLink size={10} />
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function DraftSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[100, 85, 92, 70, 95, 80].map((w, i) => (
        <div key={i} className="skeleton h-4 rounded" style={{ width: `${w}%` }} />
      ))}
      <div className="h-6" />
      {[88, 75, 90].map((w, i) => (
        <div key={i} className="skeleton h-4 rounded" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

export default function AnalyzeView({
  selectedDocId,
  selectedDocName,
  onDraftGenerated,
}: AnalyzeViewProps) {
  const [query, setQuery] = useState('');
  const [nResults, setNResults] = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [draftResult, setDraftResult] = useState<DraftResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [useFewShot, setUseFewShot] = useState(true);
  const [useProfile, setUseProfile] = useState(true);

  const handleGenerate = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setDraftResult(null);

    try {
      const result = await generateDraft(
        query.trim(),
        nResults,
        selectedDocId || null,
        useFewShot,
        useProfile
      );
      setDraftResult(result);
      onDraftGenerated(result, query.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Draft generation failed.');
    } finally {
      setLoading(false);
    }
  }, [query, nResults, selectedDocId, useFewShot, useProfile, onDraftGenerated]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleGenerate();
    }
  };

  const handleCopy = () => {
    if (draftResult?.draft) {
      navigator.clipboard.writeText(draftResult.draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!draftResult?.draft) return;
    const blob = new Blob([draftResult.draft], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `draft-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Legal Draft Generation</h1>
        <p className="text-sm text-text-secondary mt-1">
          AI-powered drafting grounded in your document corpus
        </p>
      </div>

      {/* Scope Banner */}
      <div
        className={clsx(
          'flex items-center gap-3 px-4 py-3 rounded-lg border text-sm',
          selectedDocId
            ? 'bg-primary/10 border-primary/30 text-primary-hover'
            : 'bg-bg-card border-border text-text-secondary'
        )}
      >
        <FileText size={16} className={selectedDocId ? 'text-primary' : 'text-text-muted'} />
        <span>
          {selectedDocId ? (
            <>
              Scoped to:{' '}
              <span className="font-semibold text-text-primary">{selectedDocName}</span>
            </>
          ) : (
            'Searching across all indexed documents'
          )}
        </span>
        {selectedDocId && (
          <span className="ml-auto text-xs text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
            Filtered
          </span>
        )}
      </div>

      {/* Query Input */}
      <div className="bg-bg-card border border-border rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-semibold text-text-primary flex items-center gap-2">
            <Sparkles size={14} className="text-accent-gold" />
            Matter Description
          </label>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={clsx(
              'flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all',
              showSettings
                ? 'bg-primary/10 border-primary/30 text-primary'
                : 'border-border text-text-muted hover:text-text-secondary hover:border-border'
            )}
          >
            <SlidersHorizontal size={12} />
            Settings
          </button>
        </div>

        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the matter or question to analyze... (Ctrl+Enter to generate)"
          rows={4}
          className="w-full bg-bg-primary border border-border rounded-lg px-4 py-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary resize-none leading-relaxed transition-colors"
        />

        {/* Settings panel */}
        {showSettings && (
          <div className="bg-bg-primary border border-border rounded-lg p-4 space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-xs font-medium text-text-secondary">
                  Source References
                </label>
                <span className="text-xs font-bold text-primary">{nResults}</span>
              </div>
              <input
                type="range"
                min={3}
                max={15}
                value={nResults}
                onChange={(e) => setNResults(Number(e.target.value))}
                className="w-full accent-primary"
              />
              <div className="flex justify-between text-xs text-text-muted mt-1">
                <span>3 (focused)</span>
                <span>15 (comprehensive)</span>
              </div>
            </div>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useFewShot}
                  onChange={(e) => setUseFewShot(e.target.checked)}
                  className="accent-primary"
                />
                <span className="text-xs text-text-secondary">Use few-shot examples</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useProfile}
                  onChange={(e) => setUseProfile(e.target.checked)}
                  className="accent-primary"
                />
                <span className="text-xs text-text-secondary">Apply operator profile</span>
              </label>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 p-3 bg-error/10 border border-error/30 rounded-lg text-error-light text-sm">
            <AlertCircle size={16} className="flex-shrink-0" />
            <span>{error}</span>
            <button onClick={() => setError('')} className="ml-auto">
              <X size={16} />
            </button>
          </div>
        )}

        <button
          onClick={handleGenerate}
          disabled={!query.trim() || loading}
          className={clsx(
            'w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-150',
            !query.trim() || loading
              ? 'bg-primary/30 text-white/40 cursor-not-allowed'
              : 'bg-primary hover:bg-primary-hover text-white shadow-lg shadow-primary/20 hover:shadow-primary/30'
          )}
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Generating Draft...
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Generate Draft
            </>
          )}
        </button>
      </div>

      {/* Results area */}
      {(loading || draftResult) && (
        <div className="grid grid-cols-3 gap-5">
          {/* Draft panel (2/3) */}
          <div className="col-span-2">
            <div className="bg-bg-card border border-border rounded-xl overflow-hidden h-full">
              <div className="flex items-center justify-between px-5 py-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <FileText size={15} className="text-primary" />
                  <span className="text-sm font-semibold text-text-primary">Generated Draft</span>
                  {draftResult?.preferences_applied && (
                    <span className="text-xs px-2 py-0.5 bg-success/10 border border-success/30 text-success-light rounded-full">
                      Profile Applied
                    </span>
                  )}
                </div>
                {draftResult && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-border text-text-secondary hover:text-text-primary hover:border-border transition-all"
                    >
                      {copied ? <CheckCheck size={13} className="text-success-light" /> : <Copy size={13} />}
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                    <button
                      onClick={handleDownload}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-border text-text-secondary hover:text-text-primary hover:border-border transition-all"
                    >
                      <Download size={13} />
                      Download .md
                    </button>
                  </div>
                )}
              </div>
              <div className="p-5 overflow-y-auto max-h-[70vh]">
                {loading ? (
                  <DraftSkeleton />
                ) : draftResult ? (
                  <div className="prose-legal">
                    <ReactMarkdown>{draftResult.draft}</ReactMarkdown>
                  </div>
                ) : null}
              </div>
            </div>
          </div>

          {/* Sources panel (1/3) */}
          <div className="col-span-1">
            <div className="bg-bg-card border border-border rounded-xl overflow-hidden h-full">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <BookOpen size={15} className="text-accent-gold" />
                  <span className="text-sm font-semibold text-text-primary">Evidence</span>
                </div>
                {draftResult && (
                  <span className="text-xs text-text-muted">
                    {draftResult.evidence_used} sources
                  </span>
                )}
              </div>
              <div className="p-4 space-y-3 overflow-y-auto max-h-[70vh]">
                {loading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="bg-bg-primary rounded-lg p-3 space-y-2">
                        <div className="skeleton h-3 rounded w-3/4" />
                        <div className="skeleton h-2 rounded w-full" />
                        <div className="skeleton h-2 rounded w-5/6" />
                      </div>
                    ))}
                  </div>
                ) : draftResult?.sources && draftResult.sources.length > 0 ? (
                  draftResult.sources.map((source) => (
                    <SourceCard key={source.source_number} source={source} />
                  ))
                ) : (
                  <div className="text-center py-8 text-text-muted">
                    <BookOpen size={24} className="mx-auto mb-2 opacity-40" />
                    <p className="text-xs">No sources available</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !draftResult && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-20 h-20 bg-bg-card border border-border rounded-2xl flex items-center justify-center mb-5">
            <Search size={36} className="text-text-muted opacity-40" />
          </div>
          <h3 className="text-lg font-semibold text-text-secondary mb-2">
            Ready to analyze
          </h3>
          <p className="text-sm text-text-muted max-w-md">
            Enter a legal matter description above and click{' '}
            <strong className="text-text-secondary">Generate Draft</strong> to produce an
            AI-grounded analysis with cited evidence from your document corpus.
          </p>
          <div className="mt-6 grid grid-cols-3 gap-3 max-w-lg text-left">
            {[
              'Summarize key contractual obligations in the NDA',
              'Identify indemnification clauses and their scope',
              'What are the termination conditions and notice periods?',
            ].map((example) => (
              <button
                key={example}
                onClick={() => setQuery(example)}
                className="px-3 py-2.5 bg-bg-card border border-border rounded-lg text-xs text-text-muted hover:text-text-secondary hover:border-border hover:bg-bg-card-hover transition-all text-left"
              >
                &ldquo;{example}&rdquo;
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
