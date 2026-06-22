import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/api';
import { repoService } from '../../services/endpoints';
import {
  GitCompare, ArrowLeftRight, AlertTriangle, CheckCircle,
  TrendingUp, TrendingDown, Layers, Code2, ShieldAlert,
  Wrench, FileCode
} from 'lucide-react';

function DeltaBadge({ change }: { change: number }) {
  if (change > 0) {
    return (
      <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
        <TrendingUp size={10} /> +{change}%
      </span>
    );
  }
  if (change < 0) {
    return (
      <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 border border-red-500/20 text-red-400">
        <TrendingDown size={10} /> {change}%
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-zinc-800 border border-zinc-700 text-zinc-400">
      No Change
    </span>
  );
}

function StatDeltaBadge({ change, suffix = '', inverse = false }: { change: number; suffix?: string; inverse?: boolean }) {
  if (change === 0) return null;
  const isPositive = change > 0;
  // If inverse is true (like findings or debt hours), positive is bad (red), negative is good (green)
  const isGood = inverse ? !isPositive : isPositive;
  const colorClass = isGood
    ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
    : 'text-red-400 bg-red-500/10 border-red-500/20';

  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold border ${colorClass}`}>
      {isPositive ? '+' : ''}{change}{suffix}
    </span>
  );
}

export default function RepoComparePage() {
  const { id } = useParams<{ id: string }>();
  const [selectedRepoId, setSelectedRepoId] = useState<string>('');
  const [compareId, setCompareId] = useState<string>('');

  // Fetch all repositories to list for comparison
  const { data: repositories = [] } = useQuery({
    queryKey: ['repositories'],
    queryFn: repoService.list,
  });

  // Filter current repository from list
  const otherRepos = repositories.filter(r => r.id !== id && r.status === 'COMPLETE');

  // Fetch comparison results
  const { data: comparison, isLoading, error } = useQuery({
    queryKey: ['comparison', id, compareId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/collab/compare/${id}/${compareId}`);
      return data;
    },
    enabled: !!id && !!compareId,
    staleTime: 30000,
  });

  const handleCompare = () => {
    if (selectedRepoId) {
      setCompareId(selectedRepoId);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 text-zinc-100 p-6 md:p-8 space-y-6">
      {/* Header */}
      <div className="border-b border-zinc-800/60 pb-5">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <GitCompare size={20} className="text-violet-400" />
          Repository Snapshot Comparison
        </h1>
        <p className="text-xs text-zinc-500 mt-1">
          Compare security scores, code quality dimensions, technical debt, and find newly introduced or resolved findings between codebase snapshots.
        </p>
      </div>

      {/* Select Repo Panel */}
      <div className="glass-card border border-zinc-850 rounded-2xl p-5 bg-zinc-900/10 flex flex-col sm:flex-row items-end gap-4">
        <div className="flex-1 space-y-1.5 w-full">
          <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">
            Select Repository to Compare Against (Head Snapshot)
          </label>
          <select
            value={selectedRepoId}
            onChange={(e) => setSelectedRepoId(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-850 rounded-xl px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-violet-500/60"
          >
            <option value="">-- Choose Repository --</option>
            {otherRepos.map(r => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.branch})
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={handleCompare}
          disabled={!selectedRepoId}
          className="w-full sm:w-auto px-5 py-2 rounded-xl text-xs font-bold bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:border-zinc-800 text-white transition-all flex items-center justify-center gap-1.5 shrink-0"
        >
          <ArrowLeftRight size={13} />
          Compare Snapshots
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-zinc-500 text-xs font-medium">Computing diff score and analyzing codebase deltas...</p>
        </div>
      )}

      {/* No selection placeholder */}
      {!compareId && !isLoading && (
        <div className="glass-card border border-zinc-850 rounded-2xl p-16 text-center">
          <GitCompare size={36} className="text-zinc-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-zinc-400">Select a Head Snapshot</h3>
          <p className="text-xs text-zinc-600 mt-1 max-w-sm mx-auto">
            Choose another branch snapshot or post-refactored codebase ingestion to see structural, security, and quality changes side-by-side.
          </p>
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="glass-card border border-red-500/20 bg-red-500/5 rounded-2xl p-8 text-center max-w-md mx-auto">
          <AlertTriangle size={32} className="text-red-400 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-zinc-200">Comparison Failed</h3>
          <p className="text-xs text-zinc-500 mt-2">Could not compute the delta between these repositories. Verify both repositories have completed analysis.</p>
        </div>
      )}

      {/* Comparison results */}
      {comparison && !isLoading && !error && (
        <div className="space-y-6">
          {/* Comparison Header */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Base repo */}
            <div className="glass-card border border-zinc-800 rounded-2xl p-4 bg-zinc-900/20 relative overflow-hidden">
              <div className="absolute right-0 top-0 text-zinc-800/10 font-bold font-mono text-8xl pointer-events-none select-none -mr-4 -mt-4">BASE</div>
              <div className="text-[10px] font-extrabold text-violet-400 uppercase tracking-widest mb-1">Base (Before)</div>
              <h3 className="text-sm font-bold text-zinc-200">{comparison.base_repo.name}</h3>
              <p className="text-[10px] text-zinc-500 font-mono mt-1">{comparison.base_repo.github_url} ({comparison.base_repo.branch})</p>
            </div>
            {/* Head repo */}
            <div className="glass-card border border-violet-500/20 rounded-2xl p-4 bg-violet-500/5 relative overflow-hidden">
              <div className="absolute right-0 top-0 text-violet-500/5 font-bold font-mono text-8xl pointer-events-none select-none -mr-4 -mt-4 font-extrabold">HEAD</div>
              <div className="text-[10px] font-extrabold text-emerald-400 uppercase tracking-widest mb-1">Head (After)</div>
              <h3 className="text-sm font-bold text-zinc-200">{comparison.head_repo.name}</h3>
              <p className="text-[10px] text-zinc-500 font-mono mt-1">{comparison.head_repo.github_url} ({comparison.head_repo.branch})</p>
            </div>
          </div>

          {/* Scores comparison */}
          <div className="glass-card border border-zinc-850 rounded-2xl p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Code2 size={14} className="text-violet-400" /> Score Card Deltas
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {Object.entries(comparison.score_changes).map(([key, value]: any) => (
                <div key={key} className="bg-zinc-950/60 border border-zinc-900 rounded-xl p-4 flex flex-col justify-between h-28">
                  <div>
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">{key} Score</span>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-2xl font-extrabold font-mono text-zinc-200">{value.head}%</span>
                      <span className="text-xs text-zinc-500 font-mono font-medium">vs {value.base}%</span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <DeltaBadge change={value.change} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Metrics comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Codebase Size */}
            <div className="glass-card border border-zinc-850 rounded-2xl p-5 space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <Layers size={14} className="text-cyan-400" /> Codebase Size
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-zinc-900 text-xs">
                  <span className="text-zinc-500 font-medium">Total Lines of Code</span>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-zinc-300 font-bold">{comparison.meta_changes.total_loc.head.toLocaleString()}</span>
                    <StatDeltaBadge change={comparison.meta_changes.total_loc.change} suffix=" LOC" />
                  </div>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-zinc-900 text-xs">
                  <span className="text-zinc-500 font-medium">Total Files</span>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-zinc-300 font-bold">{comparison.meta_changes.total_files.head}</span>
                    <StatDeltaBadge change={comparison.meta_changes.total_files.change} suffix=" files" />
                  </div>
                </div>
              </div>
            </div>

            {/* Technical Debt */}
            <div className="glass-card border border-zinc-850 rounded-2xl p-5 space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <Wrench size={14} className="text-amber-400" /> Technical Debt
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-zinc-900 text-xs">
                  <span className="text-zinc-500 font-medium">Total Review Findings</span>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-zinc-300 font-bold">{comparison.debt_changes.findings_count.head}</span>
                    <StatDeltaBadge change={comparison.debt_changes.findings_count.change} inverse={true} />
                  </div>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-zinc-900 text-xs">
                  <span className="text-zinc-500 font-medium">Estimated Refactor Time</span>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-zinc-300 font-bold">{comparison.debt_changes.hours.head.toFixed(1)}h</span>
                    <StatDeltaBadge change={comparison.debt_changes.hours.change} suffix="h" inverse={true} />
                  </div>
                </div>
              </div>
            </div>

            {/* Severity Deltas */}
            <div className="glass-card border border-zinc-850 rounded-2xl p-5 space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <ShieldAlert size={14} className="text-red-400" /> Severity Breakdown
              </h2>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(comparison.severity_changes).map(([sev, value]: any) => (
                  <div key={sev} className="bg-zinc-900/40 border border-zinc-850/60 rounded-xl p-2.5 flex justify-between items-center">
                    <div>
                      <span className="text-[9px] uppercase font-bold text-zinc-500">{sev}</span>
                      <div className="font-bold text-zinc-300 mt-0.5">{value.head} <span className="text-[10px] text-zinc-650 font-normal font-mono">vs {value.base}</span></div>
                    </div>
                    <StatDeltaBadge change={value.change} inverse={true} />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Finding list comparisons */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Resolved Findings */}
            <div className="glass-card border border-emerald-500/10 rounded-2xl p-5 space-y-4 bg-emerald-500/5 flex flex-col max-h-[500px]">
              <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center justify-between shrink-0">
                <span className="flex items-center gap-2">
                  <CheckCircle size={14} /> Resolved Issues
                </span>
                <span className="text-[10px] bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30 font-bold">{comparison.resolved_findings.length} fixed</span>
              </h2>

              <div className="overflow-y-auto divide-y divide-emerald-500/10 flex-1 pr-1 space-y-3">
                {comparison.resolved_findings.length === 0 ? (
                  <div className="text-xs text-zinc-500 py-10 text-center">No existing issues resolved in head snapshot.</div>
                ) : (
                  comparison.resolved_findings.map((f: any) => (
                    <div key={f.id} className="pt-3 first:pt-0 pb-1 text-xs">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-[10px] font-bold text-zinc-200">{f.category}</span>
                        <span className="badge badge-emerald text-[9px]">{f.severity}</span>
                      </div>
                      <h4 className="font-bold text-zinc-300 leading-snug">{f.title}</h4>
                      <p className="text-zinc-500 mt-1 leading-normal text-[11px]">{f.description}</p>
                      <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-500 mt-2">
                        <FileCode size={11} />
                        <span>{f.file_path}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* New Findings */}
            <div className="glass-card border border-red-500/10 rounded-2xl p-5 space-y-4 bg-red-500/5 flex flex-col max-h-[500px]">
              <h2 className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center justify-between shrink-0">
                <span className="flex items-center gap-2">
                  <AlertTriangle size={14} /> Newly Introduced Issues
                </span>
                <span className="text-[10px] bg-red-500/15 px-2 py-0.5 rounded border border-red-500/30 font-bold">{comparison.new_findings.length} new</span>
              </h2>

              <div className="overflow-y-auto divide-y divide-red-500/10 flex-1 pr-1 space-y-3">
                {comparison.new_findings.length === 0 ? (
                  <div className="text-xs text-zinc-500 py-10 text-center">No new security vulnerabilities or code smells introduced.</div>
                ) : (
                  comparison.new_findings.map((f: any) => (
                    <div key={f.id} className="pt-3 first:pt-0 pb-1 text-xs">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-[10px] font-bold text-zinc-200">{f.category}</span>
                        <span className="badge badge-red text-[9px]">{f.severity}</span>
                      </div>
                      <h4 className="font-bold text-zinc-300 leading-snug">{f.title}</h4>
                      <p className="text-zinc-500 mt-1 leading-normal text-[11px]">{f.description}</p>
                      <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-500 mt-2">
                        <FileCode size={11} />
                        <span>{f.file_path}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
