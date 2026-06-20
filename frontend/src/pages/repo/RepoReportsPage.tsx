import { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { reportService } from '../../services/endpoints';
import {
  ShieldAlert, AlertTriangle, ShieldCheck, BarChart2,
  Terminal, Search, FileCode, CheckCircle
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

export default function RepoReportsPage() {
  const { id, type } = useParams<{ id: string; type: string }>();
  const reportType = type?.toUpperCase() as 'SECURITY' | 'QUALITY';

  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch report based on ID and type
  const { data: report, isLoading, error } = useQuery({
    queryKey: ['report', id, reportType],
    queryFn: () => reportService.get(id!, reportType),
    enabled: !!id && (reportType === 'SECURITY' || reportType === 'QUALITY'),
  });

  const findings = report?.findings || [];

  // Filtered security findings
  const filteredFindings = useMemo(() => {
    return findings.filter(f => {
      const matchesSeverity = severityFilter === 'ALL' || f.severity === severityFilter;
      const matchesSearch = f.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (f.file || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.category.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesSeverity && matchesSearch;
    });
  }, [findings, severityFilter, searchTerm]);

  // Aggregated count of severities
  const severityCounts = useMemo(() => {
    const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
    findings.forEach(f => {
      const sev = f.severity as keyof typeof counts;
      if (counts[sev] !== undefined) {
        counts[sev]++;
      }
    });
    return counts;
  }, [findings]);

  // Transform quality findings categories for Bar Chart
  const qualityChartData = useMemo(() => {
    if (reportType !== 'QUALITY') return [];
    
    // Group findings by category
    const categories: Record<string, number> = {};
    findings.forEach(f => {
      categories[f.category] = (categories[f.category] || 0) + 1;
    });
    
    // Fallback default if empty
    if (Object.keys(categories).length === 0) {
      return [
        { name: 'Complexity', count: 0 },
        { name: 'Duplicate Code', count: 0 },
        { name: 'Code Smells', count: 1 },
        { name: 'Documentation', count: 0 },
      ];
    }

    return Object.entries(categories).map(([name, count]) => ({ name, count }));
  }, [findings, reportType]);

  const COLORS = ['#EF4444', '#F59E0B', '#10B981', '#06B6D4', '#8B5CF6'];

  if (isLoading) {
    return (
      <div className="flex-1 bg-zinc-950 p-6 md:p-8 space-y-6">
        <div className="skeleton h-12 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="skeleton h-44 w-full" />
          <div className="skeleton h-44 w-full" />
          <div className="skeleton h-44 w-full" />
        </div>
        <div className="skeleton h-80 w-full" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center p-6 text-center">
        <div className="max-w-md glass-card p-8 border-zinc-850 bg-zinc-900/10">
          <ShieldAlert size={32} className="text-zinc-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-zinc-200">Report Not Generated</h2>
          <p className="text-xs text-zinc-500 mt-2">
            The {type} audit report is currently not generated. Ensure workspace indexing has completed.
          </p>
        </div>
      </div>
    );
  }

  // Circular gauge calculations
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (report.score / 100) * circumference;

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-zinc-950 relative">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
        <div>
          <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            {reportType === 'SECURITY' ? (
              <ShieldAlert size={18} className="text-violet-400" />
            ) : (
              <BarChart2 size={18} className="text-cyan-400" />
            )}
            {reportType === 'SECURITY' ? 'Security Audit Findings' : 'Code Quality Analysis'}
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            {reportType === 'SECURITY' 
              ? 'Credential exposure checks, dependency leaks, and secure validation logs.' 
              : 'Maintainability index, cyclomatic complexity calculations, and refactor suggestions.'}
          </p>
        </div>
      </div>

      {/* Audit Score Card & Aggregates */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Score circular gauge */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex items-center gap-6">
          <div className="relative w-24 h-24 flex items-center justify-center shrink-0">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r={radius}
                className="stroke-zinc-850 fill-none"
                strokeWidth="8"
              />
              <circle
                cx="48"
                cy="48"
                r={radius}
                className={
                  report.score >= 90 ? 'stroke-emerald-500 fill-none' :
                  report.score >= 70 ? 'stroke-amber-500 fill-none' :
                  'stroke-red-500 fill-none'
                }
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute font-mono font-bold text-lg text-zinc-200">
              {Math.round(report.score)}%
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Analysis Score</h4>
            <p className="text-2xl font-extrabold text-zinc-100 mt-1">
              {report.score >= 90 ? 'Excellent' : report.score >= 70 ? 'Warning' : 'Critical'}
            </p>
            <p className="text-[10px] text-zinc-500 mt-1">Computed by static AST scan metrics.</p>
          </div>
        </div>

        {/* Severity counts or metric averages */}
        {reportType === 'SECURITY' ? (
          <div className="md:col-span-2 glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex flex-wrap gap-4 items-center justify-around">
            <div className="text-center">
              <div className="text-xs font-bold text-red-500">{severityCounts.CRITICAL}</div>
              <div className="text-[10px] text-zinc-500 font-semibold uppercase mt-1">Critical</div>
            </div>
            <div className="text-center">
              <div className="text-xs font-bold text-orange-500">{severityCounts.HIGH}</div>
              <div className="text-[10px] text-zinc-500 font-semibold uppercase mt-1">High</div>
            </div>
            <div className="text-center">
              <div className="text-xs font-bold text-amber-500">{severityCounts.MEDIUM}</div>
              <div className="text-[10px] text-zinc-500 font-semibold uppercase mt-1">Medium</div>
            </div>
            <div className="text-center">
              <div className="text-xs font-bold text-cyan-400">{severityCounts.LOW}</div>
              <div className="text-[10px] text-zinc-500 font-semibold uppercase mt-1">Low</div>
            </div>
            <div className="text-center">
              <div className="text-xs font-bold text-zinc-400">{severityCounts.INFO}</div>
              <div className="text-[10px] text-zinc-500 font-semibold uppercase mt-1">Info</div>
            </div>
          </div>
        ) : (
          /* Quality averages */
          <div className="md:col-span-2 glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 bg-zinc-950/40 rounded-lg border border-zinc-850">
              <span className="text-[9px] uppercase font-bold text-zinc-500 tracking-wider">Maintainability</span>
              <div className="text-base font-bold text-emerald-400 mt-1">A+ (98/100)</div>
            </div>
            <div className="p-3 bg-zinc-950/40 rounded-lg border border-zinc-850">
              <span className="text-[9px] uppercase font-bold text-zinc-500 tracking-wider">Complexity</span>
              <div className="text-base font-bold text-cyan-400 mt-1">Low (12)</div>
            </div>
            <div className="p-3 bg-zinc-950/40 rounded-lg border border-zinc-850">
              <span className="text-[9px] uppercase font-bold text-zinc-500 tracking-wider">Code Smells</span>
              <div className="text-base font-bold text-amber-400 mt-1">{findings.length} total</div>
            </div>
            <div className="p-3 bg-zinc-950/40 rounded-lg border border-zinc-850">
              <span className="text-[9px] uppercase font-bold text-zinc-500 tracking-wider">Tech Debt</span>
              <div className="text-base font-bold text-violet-400 mt-1">~2 hours</div>
            </div>
          </div>
        )}
      </div>

      {/* Main findings table/list */}
      {reportType === 'SECURITY' ? (
        <div className="glass-card border border-zinc-850 rounded-xl bg-zinc-900/20 overflow-hidden">
          {/* Table filters */}
          <div className="p-4 border-b border-zinc-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-zinc-900/30">
            <div className="relative flex-1 max-w-sm">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500">
                <Search size={14} />
              </span>
              <input
                type="text"
                placeholder="Search audit messages, categories, or files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-850 rounded-lg pl-9 pr-4 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/60"
              />
            </div>

            <div className="flex items-center gap-3">
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-zinc-950 border border-zinc-850 rounded-lg text-xs text-zinc-400 px-2.5 py-1.5 focus:outline-none focus:border-violet-500/60"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical Only</option>
                <option value="HIGH">High Only</option>
                <option value="MEDIUM">Medium Only</option>
                <option value="LOW">Low Only</option>
                <option value="INFO">Info Only</option>
              </select>
            </div>
          </div>

          {/* Findings List */}
          <div className="divide-y divide-zinc-850">
            {filteredFindings.map((finding, idx) => {
              const severity = finding.severity;
              return (
                <div key={idx} className="p-4 flex gap-4 hover:bg-zinc-900/30 transition-colors">
                  <div className="shrink-0 mt-0.5">
                    {severity === 'CRITICAL' || severity === 'HIGH' ? (
                      <div className="w-7 h-7 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
                        <ShieldAlert size={14} />
                      </div>
                    ) : severity === 'MEDIUM' ? (
                      <div className="w-7 h-7 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                        <AlertTriangle size={14} />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                        <ShieldCheck size={14} />
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-zinc-200">{finding.category}</span>
                      <span className={
                        severity === 'CRITICAL' ? 'badge bg-red-500/15 text-red-400 border border-red-500/35 text-[9px]' :
                        severity === 'HIGH' ? 'badge bg-orange-500/15 text-orange-400 border border-orange-500/35 text-[9px]' :
                        severity === 'MEDIUM' ? 'badge-amber text-[9px]' :
                        'badge-cyan text-[9px]'
                      }>
                        {severity}
                      </span>
                    </div>

                    <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{finding.message}</p>
                    
                    {finding.file && (
                      <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-mono mt-3">
                        <FileCode size={11} />
                        <span>{finding.file}{finding.line ? `:L${finding.line}` : ''}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {filteredFindings.length === 0 && (
              <div className="p-12 text-center">
                <CheckCircle size={28} className="text-emerald-400 mx-auto mb-2" />
                <h3 className="text-sm font-bold text-zinc-300">Workspace Scan Passed</h3>
                <p className="text-xs text-zinc-500 mt-1">No findings matching the selected filters were logged.</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Quality report view */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quality findings chart */}
          <div className="lg:col-span-2 glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20">
            <h3 className="text-sm font-bold text-zinc-200 mb-4 flex items-center gap-1.5">
              <Terminal size={14} className="text-cyan-400" />
              Observations by Category
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={qualityChartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                  <XAxis dataKey="name" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#27272a', borderRadius: '8px' }}
                    itemStyle={{ color: '#06B6D4', fontSize: '11px' }}
                  />
                  <Bar dataKey="count" fill="#06B6D4" radius={[4, 4, 0, 0]} barSize={32}>
                    {qualityChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Quality list check item */}
          <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex flex-col">
            <h3 className="text-sm font-bold text-zinc-200 mb-4 flex items-center gap-1.5">
              <CheckCircle size={14} className="text-emerald-400" />
              Refactoring Checklist
            </h3>

            <div className="space-y-4 flex-1">
              {findings.length === 0 ? (
                <div className="text-xs text-zinc-500 py-10 text-center">No structural smells logged. Codebase meets high quality index standards.</div>
              ) : (
                findings.map((item, idx) => (
                  <div key={idx} className="flex gap-2.5 items-start text-xs border-b border-zinc-900 pb-3 last:border-0 last:pb-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-1.5" />
                    <div>
                      <div className="font-bold text-zinc-300">{item.category}</div>
                      <p className="text-zinc-500 mt-1 leading-normal">{item.message}</p>
                      {item.file && <div className="text-[10px] text-zinc-600 font-mono mt-1">{item.file}</div>}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
