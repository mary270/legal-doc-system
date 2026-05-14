'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  BarChart2,
  TrendingUp,
  TrendingDown,
  Minus,
  Star,
  UserCircle,
  Loader2,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  XCircle,
  BookOpen,
  Clock,
  ChevronDown,
  ChevronUp,
  X,
  Zap,
} from 'lucide-react';
import clsx from 'clsx';
import {
  getMetrics,
  getMetricsSummary,
  getAllPreferences,
  deactivatePreference,
  getProfile,
  buildProfile,
  getFewShotExamples,
} from '@/lib/api';
import type {
  MetricEntry,
  MetricsSummary,
  Preference,
  Profile,
  FewShotExample,
} from '@/lib/types';

function SummaryCard({
  label,
  value,
  sub,
  icon,
  colorClass = 'text-text-primary',
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  colorClass?: string;
}) {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-5 hover:bg-bg-card-hover transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
          {label}
        </span>
        <span className="text-text-muted">{icon}</span>
      </div>
      <p className={clsx('text-3xl font-bold', colorClass)}>{value}</p>
      {sub && <p className="text-xs text-text-muted mt-1.5">{sub}</p>}
    </div>
  );
}

function TrendBadge({ trend, early, late }: { trend: string; early: number; late: number }) {
  const isUp = late > early;
  const isFlat = Math.abs(late - early) < 2;
  return (
    <div
      className={clsx(
        'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
        isFlat
          ? 'bg-text-muted/10 text-text-muted'
          : isUp
          ? 'bg-success/10 text-success-light border border-success/20'
          : 'bg-error/10 text-error-light border border-error/20'
      )}
    >
      {isFlat ? <Minus size={12} /> : isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
      {trend || (isFlat ? 'Stable' : isUp ? 'Improving' : 'Declining')}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 75
      ? 'bg-success/10 text-success-light border-success/20'
      : score >= 50
      ? 'bg-accent-gold/10 text-accent-gold-light border-accent-gold/20'
      : 'bg-error/10 text-error-light border-error/20';
  return (
    <span className={clsx('px-2 py-0.5 rounded text-xs font-bold border', color)}>
      {score.toFixed(1)}
    </span>
  );
}

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return ts;
  }
}

export default function IntelligenceView() {
  const [metrics, setMetrics] = useState<MetricEntry[]>([]);
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [preferences, setPreferences] = useState<Preference[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [fewShot, setFewShot] = useState<FewShotExample[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deactivatingIdx, setDeactivatingIdx] = useState<number | null>(null);
  const [buildingProfile, setBuildingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState('');
  const [showAllMetrics, setShowAllMetrics] = useState(false);
  const [expandedFewShot, setExpandedFewShot] = useState<number | null>(null);

  const loadAll = useCallback(async () => {
    setError('');
    try {
      const [m, s, p, prof, fs] = await Promise.allSettled([
        getMetrics(),
        getMetricsSummary(),
        getAllPreferences(),
        getProfile(),
        getFewShotExamples(),
      ]);

      if (m.status === 'fulfilled') setMetrics(m.value);
      if (s.status === 'fulfilled') setSummary(s.value);
      if (p.status === 'fulfilled') setPreferences(p.value);
      if (prof.status === 'fulfilled') setProfile(prof.value);
      if (fs.status === 'fulfilled') setFewShot(fs.value);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load intelligence data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const handleDeactivate = async (index: number) => {
    setDeactivatingIdx(index);
    try {
      await deactivatePreference(index);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deactivate preference.');
    } finally {
      setDeactivatingIdx(null);
    }
  };

  const handleBuildProfile = async () => {
    setBuildingProfile(true);
    setProfileMessage('');
    try {
      const res = await buildProfile();
      setProfileMessage(res.message || res.status || 'Profile rebuilt successfully.');
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Profile build failed.');
    } finally {
      setBuildingProfile(false);
    }
  };

  const displayedMetrics = showAllMetrics ? metrics : metrics.slice(0, 10);
  const activePrefs = preferences.filter((p) => p.active);
  const inactivePrefs = preferences.filter((p) => !p.active);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full py-32">
        <div className="text-center space-y-3">
          <Loader2 size={32} className="text-primary animate-spin mx-auto" />
          <p className="text-text-secondary text-sm">Loading intelligence data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Intelligence Dashboard</h1>
          <p className="text-sm text-text-secondary mt-1">
            Performance metrics, learned preferences, and operator profile
          </p>
        </div>
        <button
          onClick={loadAll}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-border rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-card transition-all"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
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

      {/* ── Section 1: Metrics Summary ── */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <BarChart2 size={16} className="text-primary" />
          <h2 className="text-base font-bold text-text-primary">Performance Summary</h2>
        </div>
        {summary ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <SummaryCard
                label="Total Edit Sessions"
                value={summary.total_edits}
                sub="Completed training rounds"
                icon={<BookOpen size={16} />}
                colorClass="text-primary-hover"
              />
              <SummaryCard
                label="Avg Improvement Score"
                value={`${summary.avg_improvement_score.toFixed(1)}`}
                sub="Across all edit sessions"
                icon={<Star size={16} />}
                colorClass={
                  summary.avg_improvement_score >= 75
                    ? 'text-success-light'
                    : summary.avg_improvement_score >= 50
                    ? 'text-accent-gold-light'
                    : 'text-error-light'
                }
              />
              <SummaryCard
                label="Avg Content Retained"
                value={`${summary.avg_retained_pct.toFixed(1)}%`}
                sub="Mean retention rate"
                icon={<CheckCircle size={16} />}
                colorClass="text-text-primary"
              />
              <div className="bg-bg-card border border-border rounded-xl p-5 hover:bg-bg-card-hover transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Score Trend
                  </span>
                  <span className="text-text-muted">
                    <TrendingUp size={16} />
                  </span>
                </div>
                <TrendBadge
                  trend={summary.score_trend}
                  early={summary.early_avg_score}
                  late={summary.late_avg_score}
                />
                <p className="text-xs text-text-muted mt-2">
                  Early: {summary.early_avg_score.toFixed(1)} → Late:{' '}
                  {summary.late_avg_score.toFixed(1)}
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-bg-card border border-border rounded-xl p-8 text-center">
            <BarChart2 size={32} className="text-text-muted opacity-40 mx-auto mb-3" />
            <p className="text-text-secondary text-sm">No performance data yet</p>
            <p className="text-text-muted text-xs mt-1">Submit edits in the Learn tab to generate metrics</p>
          </div>
        )}
      </section>

      {/* ── Section 2: Edit History ── */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-accent-gold" />
            <h2 className="text-base font-bold text-text-primary">Edit History</h2>
          </div>
          {metrics.length > 10 && (
            <button
              onClick={() => setShowAllMetrics(!showAllMetrics)}
              className="flex items-center gap-1 text-xs text-primary hover:text-primary-hover"
            >
              {showAllMetrics ? (
                <>
                  <ChevronUp size={13} /> Show less
                </>
              ) : (
                <>
                  <ChevronDown size={13} /> Show all ({metrics.length})
                </>
              )}
            </button>
          )}
        </div>

        <div className="bg-bg-card border border-border rounded-xl overflow-hidden">
          {metrics.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Clock size={28} className="text-text-muted opacity-40 mb-3" />
              <p className="text-text-secondary text-sm">No edit sessions recorded yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-bg-primary/50">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                      Query
                    </th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                      Score
                    </th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                      Retained
                    </th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                      Edit Dist.
                    </th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">
                      Changed
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-subtle">
                  {displayedMetrics.map((entry, i) => (
                    <tr
                      key={i}
                      className={clsx(
                        'transition-colors duration-100',
                        entry.improvement_score >= 75
                          ? 'hover:bg-success/5'
                          : entry.improvement_score >= 50
                          ? 'hover:bg-accent-gold/5'
                          : 'hover:bg-bg-card-hover'
                      )}
                    >
                      <td className="px-5 py-3 text-xs text-text-muted whitespace-nowrap">
                        {formatTimestamp(entry.timestamp)}
                      </td>
                      <td className="px-5 py-3 max-w-xs">
                        <p className="text-xs text-text-secondary truncate">{entry.query}</p>
                      </td>
                      <td className="px-5 py-3 text-center">
                        <ScoreBadge score={entry.improvement_score} />
                      </td>
                      <td className="px-5 py-3 text-center text-xs text-text-secondary">
                        {entry.retained_pct.toFixed(1)}%
                      </td>
                      <td className="px-5 py-3 text-center text-xs text-text-secondary">
                        {entry.edit_distance_pct.toFixed(1)}%
                      </td>
                      <td className="px-5 py-3 text-center">
                        {entry.changed ? (
                          <CheckCircle size={14} className="text-success-light mx-auto" />
                        ) : (
                          <Minus size={14} className="text-text-muted mx-auto" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* ── Section 3: Active Preferences ── */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Star size={16} className="text-accent-gold" />
          <h2 className="text-base font-bold text-text-primary">Active Preferences</h2>
          <span className="text-xs text-text-muted bg-bg-card border border-border px-2 py-0.5 rounded">
            {activePrefs.length} active
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3">
          {activePrefs.length === 0 ? (
            <div className="bg-bg-card border border-border rounded-xl p-8 text-center">
              <Star size={28} className="text-text-muted opacity-40 mx-auto mb-3" />
              <p className="text-text-secondary text-sm">No active preferences yet</p>
              <p className="text-text-muted text-xs mt-1">
                Submit edited drafts in the Learn tab to build your preference profile
              </p>
            </div>
          ) : (
            activePrefs.map((pref, globalIdx) => {
              const originalIdx = preferences.findIndex(
                (p) => p.preference === pref.preference && p.active
              );
              return (
                <div
                  key={globalIdx}
                  className="flex items-start gap-4 p-4 bg-bg-card border border-border rounded-xl hover:bg-bg-card-hover transition-colors group"
                >
                  <div className="flex-shrink-0 w-6 h-6 bg-success/10 border border-success/30 rounded-full flex items-center justify-center">
                    <CheckCircle size={13} className="text-success-light" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-text-secondary leading-relaxed">{pref.preference}</p>
                    <div className="flex items-center gap-3 mt-2">
                      {pref.extracted_at && (
                        <span className="text-xs text-text-muted">
                          <Clock size={10} className="inline mr-1" />
                          {formatTimestamp(pref.extracted_at)}
                        </span>
                      )}
                      {pref.improvement_score_at_capture > 0 && (
                        <span className="text-xs text-text-muted">
                          Score at capture:{' '}
                          <span className="text-accent-gold-light font-medium">
                            {pref.improvement_score_at_capture.toFixed(1)}
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeactivate(originalIdx)}
                    disabled={deactivatingIdx === originalIdx}
                    className={clsx(
                      'flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 opacity-0 group-hover:opacity-100',
                      deactivatingIdx === originalIdx
                        ? 'bg-error/10 text-error-light cursor-not-allowed'
                        : 'border border-border text-text-muted hover:bg-error/10 hover:text-error-light hover:border-error/30'
                    )}
                  >
                    {deactivatingIdx === originalIdx ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <XCircle size={12} />
                    )}
                    Deactivate
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Inactive preferences (collapsed) */}
        {inactivePrefs.length > 0 && (
          <div className="mt-3 p-3 bg-bg-card border border-subtle rounded-lg">
            <p className="text-xs text-text-muted">
              {inactivePrefs.length} deactivated preference
              {inactivePrefs.length !== 1 ? 's' : ''} (hidden from active pool)
            </p>
          </div>
        )}
      </section>

      {/* ── Section 4: Operator Profile ── */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <UserCircle size={16} className="text-primary" />
            <h2 className="text-base font-bold text-text-primary">Operator Profile</h2>
          </div>
          <button
            onClick={handleBuildProfile}
            disabled={buildingProfile}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150',
              buildingProfile
                ? 'bg-primary/30 text-white/40 cursor-not-allowed'
                : 'bg-primary hover:bg-primary-hover text-white shadow-md shadow-primary/20'
            )}
          >
            {buildingProfile ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RefreshCw size={14} />
            )}
            {buildingProfile ? 'Building...' : 'Build Profile'}
          </button>
        </div>

        {profileMessage && (
          <div className="flex items-center gap-3 p-3 mb-4 bg-success/10 border border-success/30 rounded-lg text-success-light text-sm">
            <CheckCircle size={14} />
            <span>{profileMessage}</span>
            <button onClick={() => setProfileMessage('')} className="ml-auto">
              <X size={14} />
            </button>
          </div>
        )}

        {profile ? (
          <div className="grid grid-cols-2 gap-4">
            {profile.summary && (
              <div className="col-span-2 bg-bg-card border border-border rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Zap size={14} className="text-accent-gold" />
                  <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Profile Summary
                  </span>
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">{profile.summary}</p>
              </div>
            )}
            {[
              { key: 'writing_style', label: 'Writing Style', icon: '✍️' },
              { key: 'structure_preferences', label: 'Structure Preferences', icon: '📐' },
              { key: 'content_priorities', label: 'Content Priorities', icon: '🎯' },
              { key: 'avoid', label: 'What to Avoid', icon: '🚫' },
            ].map(({ key, label }) => {
              const val = profile[key as keyof Profile];
              if (!val) return null;
              return (
                <div key={key} className="bg-bg-card border border-border rounded-xl p-5">
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                    {label}
                  </p>
                  <p className="text-sm text-text-secondary leading-relaxed">{val}</p>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-bg-card border border-border rounded-xl p-10 text-center">
            <UserCircle size={36} className="text-text-muted opacity-40 mx-auto mb-4" />
            <p className="text-text-secondary font-medium mb-1">No profile built yet</p>
            <p className="text-text-muted text-sm">
              Click <strong className="text-text-secondary">Build Profile</strong> to generate your
              operator profile from edit history and preferences
            </p>
          </div>
        )}
      </section>

      {/* ── Section 5: Few-Shot Examples ── */}
      {fewShot.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <BookOpen size={16} className="text-primary" />
            <h2 className="text-base font-bold text-text-primary">Few-Shot Examples</h2>
            <span className="text-xs text-text-muted bg-bg-card border border-border px-2 py-0.5 rounded">
              {fewShot.length} saved
            </span>
          </div>
          <div className="space-y-3">
            {fewShot.map((ex, i) => (
              <div key={i} className="bg-bg-card border border-border rounded-xl overflow-hidden">
                <button
                  className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-bg-card-hover transition-colors text-left"
                  onClick={() => setExpandedFewShot(expandedFewShot === i ? null : i)}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">
                      #{i + 1}
                    </span>
                    <p className="text-sm text-text-secondary truncate">{ex.query}</p>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <ScoreBadge score={ex.improvement_score} />
                    <span className="text-xs text-text-muted">{formatTimestamp(ex.saved_at)}</span>
                    {expandedFewShot === i ? (
                      <ChevronUp size={14} className="text-text-muted" />
                    ) : (
                      <ChevronDown size={14} className="text-text-muted" />
                    )}
                  </div>
                </button>
                {expandedFewShot === i && (
                  <div className="border-t border-border p-4">
                    <pre className="text-xs text-text-secondary whitespace-pre-wrap leading-relaxed font-mono max-h-40 overflow-y-auto">
                      {ex.edited_draft}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
