import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewService } from '../../services/endpoints';
import {
  ShieldAlert, AlertTriangle, CheckCircle2, BarChart2,
  Terminal, Search, FileCode, ChevronDown, ChevronUp,
  RefreshCw, Sparkles, SlidersHorizontal, ShieldCheck
} from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

export default function RepoReviewPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFinding, setExpandedFinding] = useState<number | null>(null);

  // Fetch Code Review data
  const { data: review, isLoading, error } = useQuery({
    queryKey: ['codeReview', id],
    queryFn: () => reviewService.get(id!),
    enabled: !!id,
  });

  // Re-run review mutation
  const runReviewMutation = useMutation({
    mutationFn: () => reviewService.trigger(id!),
    onSuccess: (data) => {
      queryClient.setQueryData(['codeReview', id], data);
    },
  });

  if (isLoading) {
    return (
      <div className="flex-1 bg-zinc-950 p-6 md:p-8 space-y-6">
        <div className="skeleton h-12 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="skeleton h-32 w-full" />
          <div className="skeleton h-32 w-full" />
          <div className="skeleton h-32 w-full" />
          <div className="skeleton h-32 w-full" />
        </div>
        <div className="skeleton h-80 w-full" />
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center p-6 text-center">
        <div className="max-w-md glass-card p-8 border-zinc-850 bg-zinc-900/10">
          <ShieldAlert size={32} className="text-zinc-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-zinc-200">No Review Available</h2>
          <p className="text-xs text-zinc-500 mt-2">
            Failed to fetch or generate the code review report for this workspace.
          </p>
          <button
            onClick={() => runReviewMutation.mutate()}
            disabled={runReviewMutation.isPending}
            className="btn-primary mt-6 py-2 px-3 text-xs bg-violet-600 hover:bg-violet-500 inline-flex items-center gap-1.5"
          >
            {runReviewMutation.isPending ? (
              <RefreshCw size={14} className="animate-spin" />
            ) : (
              <Sparkles size={14} />
            )}
            Trigger Initial Review
          </button>
        </div>
      </div>
    );
  }

  const findings = review.findings || [];

  // Filter findings
  const filteredFindings = findings.filter((f: any) => {
    const matchesCategory = selectedCategory === 'ALL' || f.category === selectedCategory;
    const matchesSeverity = selectedSeverity === 'ALL' || f.severity === selectedSeverity;
    const matchesSearch =
      f.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (f.file_path || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.category.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSeverity && matchesSearch;
  });

  // Calculate counts for categories
  const categoryCounts = {
    SECURITY: findings.filter((f: any) => f.category === 'SECURITY').length,
    PERFORMANCE: findings.filter((f: any) => f.category === 'PERFORMANCE').length,
    QUALITY: findings.filter((f: any) => f.category === 'QUALITY').length,
    ARCHITECTURE: findings.filter((f: any) => f.category === 'ARCHITECTURE').length,
  };

  const severityCounts = {
    CRITICAL: findings.filter((f: any) => f.severity === 'CRITICAL').length,
    HIGH: findings.filter((f: any) => f.severity === 'HIGH').length,
    MEDIUM: findings.filter((f: any) => f.severity === 'MEDIUM').length,
    LOW: findings.filter((f: any) => f.severity === 'LOW').length,
  };

  const chartData = [
    { name: 'Security', score: review.security_score },
    { name: 'Performance', score: review.performance_score },
    { name: 'Quality', score: review.quality_score },
    { name: 'Architecture', score: review.architecture_score },
  ];

  const COLORS = ['#A78BFA', '#06B6D4', '#F59E0B', '#EF4444'];

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'HIGH':
        return 'bg-orange-500/10 border-orange-500/30 text-orange-400';
      case 'MEDIUM':
        return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
      case 'LOW':
        return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400';
      default:
        return 'bg-zinc-500/10 border-zinc-500/30 text-zinc-400';
    }
  };

  const toggleFinding = (idx: number) => {
    if (expandedFinding === idx) {
      setExpandedFinding(null);
    } else {
      setExpandedFinding(idx);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-zinc-950 text-zinc-100 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
        <div>
          <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <ShieldCheck size={22} className="text-violet-400" />
            AI Code Review Agent
          </h1>
          <p className="text-xs text-zinc-500 mt-1">
            Automated multi-agent scanner reviewing security vulnerabilities, quality smells, bottlenecks, and layers.
          </p>
        </div>

        <button
          onClick={() => runReviewMutation.mutate()}
          disabled={runReviewMutation.isPending}
          className="btn-primary py-2 px-3 text-xs bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 font-semibold inline-flex items-center gap-1.5 transition-all rounded-lg"
        >
          <RefreshCw size={12} className={runReviewMutation.isPending ? 'animate-spin' : ''} />
          {runReviewMutation.isPending ? 'Re-analyzing...' : 'Re-Run Code Review'}
        </button>
      </div>

      {/* Scores Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Overall Score */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex flex-col justify-between">
          <div>
            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Overall Health Score</h4>
            <div className="flex items-baseline gap-2 mt-4">
              <span className="text-4xl font-extrabold text-violet-400 font-mono">
                {review.overall_score}%
              </span>
              <span className="text-xs text-zinc-500 font-medium font-sans">calculated index</span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-zinc-800/50">
            <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-violet-500 to-cyan-400 h-full"
                style={{ width: `${review.overall_score}%` }}
              />
            </div>
          </div>
        </div>

        {/* Category breakdown bar charts */}
        <div className="lg:col-span-3 glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20">
          <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wide mb-4">Agent Score Summary</h4>
          <div className="h-28">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis dataKey="name" type="category" stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '11px' }}
                />
                <Bar dataKey="score" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={12}>
                  {chartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Main Review Section */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Sidebar Filters */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 space-y-5">
          <div className="flex items-center justify-between text-xs font-bold text-zinc-300 border-b border-zinc-800 pb-3">
            <span className="flex items-center gap-1.5">
              <SlidersHorizontal size={13} />
              Filter Findings
            </span>
            {findings.length > 0 && (
              <span className="text-[10px] text-zinc-500 font-mono">{filteredFindings.length} / {findings.length}</span>
            )}
          </div>

          {/* Search */}
          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Search</label>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" size={13} />
              <input
                type="text"
                placeholder="Search file, message..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-850 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/60 font-semibold"
              />
            </div>
          </div>

          {/* Categories */}
          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Category</label>
            <div className="space-y-1">
              {['ALL', 'SECURITY', 'PERFORMANCE', 'QUALITY', 'ARCHITECTURE'].map((cat) => {
                const count = cat === 'ALL' ? findings.length : (categoryCounts as any)[cat] || 0;
                return (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition-colors ${
                      selectedCategory === cat
                        ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                        : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                    }`}
                  >
                    <span>{cat}</span>
                    <span className="font-mono text-[9px] opacity-60 bg-zinc-900/60 px-1.5 py-0.5 rounded-md">{count}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Severities */}
          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Severity</label>
            <div className="space-y-1">
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => {
                const count = sev === 'ALL' ? findings.length : (severityCounts as any)[sev] || 0;
                return (
                  <button
                    key={sev}
                    onClick={() => setSelectedSeverity(sev)}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-between transition-colors ${
                      selectedSeverity === sev
                        ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                        : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                    }`}
                  >
                    <span>{sev}</span>
                    <span className="font-mono text-[9px] opacity-60 bg-zinc-900/60 px-1.5 py-0.5 rounded-md">{count}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Findings List */}
        <div className="lg:col-span-3 space-y-3">
          {filteredFindings.map((finding: any, idx: number) => {
            const isExpanded = expandedFinding === idx;
            return (
              <div
                key={idx}
                className="glass-card border border-zinc-850 rounded-xl bg-zinc-900/10 overflow-hidden hover:border-zinc-800 transition-colors"
              >
                {/* Header/Collapsible Toggle */}
                <div
                  onClick={() => toggleFinding(idx)}
                  className="p-4 flex items-start gap-3 cursor-pointer select-none"
                >
                  <div className="shrink-0 mt-0.5">
                    {finding.category === 'SECURITY' ? (
                      <ShieldAlert size={16} className="text-violet-400" />
                    ) : finding.category === 'PERFORMANCE' ? (
                      <AlertTriangle size={16} className="text-cyan-400" />
                    ) : finding.category === 'QUALITY' ? (
                      <BarChart2 size={16} className="text-amber-400" />
                    ) : (
                      <Terminal size={16} className="text-red-400" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-bold text-zinc-300">
                        {finding.category}
                      </span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase ${getSeverityBadgeClass(finding.severity)}`}>
                        {finding.severity}
                      </span>
                      {finding.file_path && (
                        <span className="text-[10px] text-zinc-500 font-mono truncate">
                          {finding.file_path}{finding.line_number ? `:L${finding.line_number}` : ''}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-300 mt-2 font-medium leading-relaxed">
                      {finding.title}
                    </p>
                  </div>

                  <div className="shrink-0 text-zinc-500">
                    {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t border-zinc-800/60 bg-zinc-900/30 p-4 space-y-4 text-xs">

                    {/* Evidence Metadata Row */}
                    <div className="grid grid-cols-2 gap-3">
                      {/* File + Line */}
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 space-y-1">
                        <div className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
                          <FileCode size={10} className="text-violet-400" />
                          Location
                        </div>
                        {finding.file_path ? (
                          <div className="font-mono text-[11px] text-zinc-200 break-all">
                            {finding.file_path}
                            {finding.line_number && (
                              <span className="ml-1 text-violet-400 font-bold">:{finding.line_number}</span>
                            )}
                          </div>
                        ) : (
                          <div className="text-zinc-600 text-[10px]">No file location</div>
                        )}
                      </div>

                      {/* Rule Triggered */}
                      <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 space-y-1">
                        <div className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
                          <ShieldCheck size={10} className="text-amber-400" />
                          Rule Triggered
                        </div>
                        <div className="font-mono text-[11px] text-amber-300 break-all">
                          {finding.rule || finding.category + ' Scan'}
                        </div>
                      </div>
                    </div>

                    {/* Reason */}
                    <div className="space-y-1">
                      <span className="flex items-center gap-1 font-bold text-violet-400 tracking-wide">
                        <Sparkles size={13} />
                        Reason / Description
                      </span>
                      <p className="text-zinc-400 leading-relaxed pl-4 border-l border-zinc-800">
                        {finding.description || 'No detailed description.'}
                      </p>
                    </div>

                    {/* Code Diff view */}
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                      {finding.code_before && finding.code_before !== '...' && (
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-bold text-red-400 uppercase flex items-center gap-1"><FileCode size={11} /> Before Code</span>
                          <div className="rounded-md overflow-hidden border border-red-500/20 bg-zinc-950">
                            <SyntaxHighlighter language="javascript" style={vscDarkPlus} customStyle={{ margin: 0, padding: '12px', fontSize: '11px', background: 'transparent' }}>
                              {finding.code_before}
                            </SyntaxHighlighter>
                          </div>
                        </div>
                      )}
                      
                      {finding.code_after && finding.code_after !== '...' && (
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-bold text-emerald-400 uppercase flex items-center gap-1"><FileCode size={11} /> Suggested Fix (After Code)</span>
                          <div className="rounded-md overflow-hidden border border-emerald-500/20 bg-zinc-950">
                            <SyntaxHighlighter language="javascript" style={vscDarkPlus} customStyle={{ margin: 0, padding: '12px', fontSize: '11px', background: 'transparent' }}>
                              {finding.code_after}
                            </SyntaxHighlighter>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {filteredFindings.length === 0 && (
            <div className="glass-card p-12 border border-zinc-850 rounded-xl bg-zinc-900/10 text-center">
              <CheckCircle2 size={36} className="text-emerald-500 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-zinc-300">All Scans Complete</h3>
              <p className="text-xs text-zinc-500 mt-1">No findings matching the selected filters were logged.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
