import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { reviewService } from '../../services/endpoints';
import {
  TrendingUp, Award, Clock, Hammer, AlertTriangle,
  FileText, Sparkles, LayoutGrid, ShieldAlert
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export default function RepoExecutiveSummaryPage() {
  const { id } = useParams<{ id: string }>();

  // Fetch Code Review data (which contains scores, cto summary, tech debt hours, etc.)
  const { data: review, isLoading, error } = useQuery({
    queryKey: ['codeReview', id],
    queryFn: () => reviewService.get(id!),
    enabled: !!id,
  });

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

  if (error || !review) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center p-6 text-center">
        <div className="max-w-md glass-card p-8 border-zinc-850 bg-zinc-900/10">
          <ShieldAlert size={32} className="text-zinc-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-zinc-200">No Summary Available</h2>
          <p className="text-xs text-zinc-500 mt-2">
            Ensure you run a Code Review first to calculate the health and executive indices.
          </p>
        </div>
      </div>
    );
  }

  // Simulated trend data (GitHub Insights/Datadog style)
  const trendData = [
    { week: 'Wk 1', health: review.overall_score - 4, coverage: 78 },
    { week: 'Wk 2', health: review.overall_score - 2, coverage: 80 },
    { week: 'Wk 3', health: review.overall_score - 3, coverage: 82 },
    { week: 'Wk 4', health: review.overall_score, coverage: review.documentation_coverage },
  ];

  // Circular gauge config helper
  const radius = 32;
  const circumference = 2 * Math.PI * radius;

  const scoreCards = [
    { label: 'Repository Health', score: review.overall_score, colorClass: 'stroke-violet-500 text-violet-400' },
    { label: 'Security Index', score: review.security_score, colorClass: 'stroke-red-500 text-red-400' },
    { label: 'Quality Index', score: review.quality_score, colorClass: 'stroke-amber-500 text-amber-400' },
    { label: 'Architecture Score', score: review.architecture_score, colorClass: 'stroke-cyan-500 text-cyan-400' },
    { label: 'Maintainability Score', score: review.maintainability_score, colorClass: 'stroke-emerald-500 text-emerald-400' },
    { label: 'Documentation Coverage', score: review.documentation_coverage, colorClass: 'stroke-violet-400 text-violet-300' },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-zinc-950 text-zinc-100 font-sans relative">
      {/* Background glow effects */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-violet-600/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-80 h-80 bg-cyan-600/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="border-b border-zinc-800/60 pb-5">
        <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
          <TrendingUp size={22} className="text-violet-400" />
          Executive Health Dashboard
        </h1>
        <p className="text-xs text-zinc-500 mt-1">
          High-level operational index, technical debt metrics, and tactical roadmap summaries for leadership.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-zinc-900/25 border border-zinc-850 rounded-xl flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-violet-500/10 border border-violet-500/15 text-violet-400">
            <Clock size={16} />
          </div>
          <div>
            <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Technical Debt</div>
            <div className="text-lg font-bold text-zinc-200 mt-0.5">{review.technical_debt_hours} hrs</div>
          </div>
        </div>

        <div className="p-4 bg-zinc-900/25 border border-zinc-850 rounded-xl flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/15 text-cyan-400">
            <Hammer size={16} />
          </div>
          <div>
            <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Engineering Effort</div>
            <div className="text-lg font-bold text-zinc-200 mt-0.5">{review.engineering_effort}</div>
          </div>
        </div>

        <div className="p-4 bg-zinc-900/25 border border-zinc-850 rounded-xl flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/15 text-amber-400">
            <AlertTriangle size={16} />
          </div>
          <div>
            <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Refactor Ops</div>
            <div className="text-lg font-bold text-zinc-200 mt-0.5">{review.refactoring_opportunities_count} areas</div>
          </div>
        </div>

        <div className="p-4 bg-zinc-900/25 border border-zinc-850 rounded-xl flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/15 text-emerald-400">
            <FileText size={16} />
          </div>
          <div>
            <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Doc Coverage</div>
            <div className="text-lg font-bold text-zinc-200 mt-0.5">{review.documentation_coverage}%</div>
          </div>
        </div>
      </div>

      {/* Circle Gauges Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {scoreCards.map((card, idx) => {
          const offset = circumference - (card.score / 100) * circumference;
          return (
            <div key={idx} className="glass-card p-4 border border-zinc-850 rounded-xl bg-zinc-900/15 flex flex-col items-center text-center justify-between">
              <span className="text-[10px] font-bold text-zinc-400 tracking-wide line-clamp-1 h-4">{card.label}</span>
              <div className="relative w-20 h-20 flex items-center justify-center my-3">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="40" cy="40" r={radius} className="stroke-zinc-850 fill-none" strokeWidth="5" />
                  <circle
                    cx="40"
                    cy="40"
                    r={radius}
                    className={`fill-none transition-all duration-500 ${card.colorClass.split(' ')[0]}`}
                    strokeWidth="5"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                  />
                </svg>
                <div className={`absolute font-mono font-extrabold text-sm ${card.colorClass.split(' ')[1]}`}>
                  {Math.round(card.score)}%
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary and Trends Split */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Summary Card */}
        <div className="lg:col-span-3 glass-card p-6 border border-zinc-850 rounded-xl bg-zinc-900/20 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <Award size={100} />
          </div>
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-violet-400 tracking-wider uppercase mb-3">
              <Sparkles size={14} />
              CTO Executive Summary
            </div>
            <p className="text-sm text-zinc-300 leading-relaxed font-medium">
              "{review.summary}"
            </p>
          </div>

          <div className="mt-6 pt-5 border-t border-zinc-800/80 flex flex-wrap gap-4 text-zinc-500 text-[10px] font-mono">
            <div>AUDITED: {new Date(review.created_at).toLocaleDateString()}</div>
            <div>VERDICT: {review.overall_score >= 80 ? 'APPROVED BUILD' : 'REFRACTOR MANDATED'}</div>
          </div>
        </div>

        {/* Trend Area Chart */}
        <div className="lg:col-span-2 glass-card p-6 border border-zinc-850 rounded-xl bg-zinc-900/20 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-zinc-400 tracking-wider uppercase mb-4">
              <LayoutGrid size={14} />
              Health & Coverage Trend
            </div>
            <div className="h-36">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                  <XAxis dataKey="week" stroke="#52525b" fontSize={9} tickLine={false} axisLine={false} />
                  <YAxis stroke="#52525b" fontSize={9} tickLine={false} axisLine={false} domain={[50, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '6px', fontSize: '10px' }} />
                  <Area type="monotone" dataKey="health" stroke="#8b5cf6" fill="url(#colorHealth)" strokeWidth={1.5} />
                  <defs>
                    <linearGradient id="colorHealth" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
