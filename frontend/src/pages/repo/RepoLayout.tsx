import { useParams, Link, useLocation, Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { repoService } from '../../services/endpoints';
import { cn } from '../../utils/cn';
import {
  Layout, FileText, Network, ShieldCheck, BarChart2,
  MessageSquare, ChevronLeft, GitBranch, RefreshCw, AlertCircle,
  Cpu, TrendingUp, Layers
} from 'lucide-react';

export default function RepoLayout() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();

  // Fetch repository detail with automatic caching
  const { data: repo, isLoading, error, refetch } = useQuery({
    queryKey: ['repository', id],
    queryFn: () => repoService.get(id!),
    enabled: !!id,
    staleTime: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-zinc-500 text-sm font-medium">Loading repository metadata...</p>
        </div>
      </div>
    );
  }

  if (error || !repo) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center p-6 text-center">
        <div className="max-w-md glass-card p-8 border-red-500/20 bg-red-500/5">
          <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
          <h2 className="text-base font-bold text-zinc-200">Repository Not Found</h2>
          <p className="text-xs text-zinc-500 mt-2">The requested workspace does not exist or you do not have permission to view it.</p>
          <Link to="/dashboard" className="btn-primary mt-6 py-2 px-3 text-xs bg-violet-600 hover:bg-violet-500 inline-flex items-center gap-1.5">
            <ChevronLeft size={14} /> Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const tabs = [
    { to: `/repositories/${id}`, label: 'Overview', icon: Layout, exact: true },
    { to: `/repositories/${id}/docs`, label: 'Documentation', icon: FileText },
    { to: `/repositories/${id}/diagrams`, label: 'Diagrams', icon: Network },
    { to: `/repositories/${id}/architecture`, label: 'Architecture Map', icon: Layers },
    { to: `/repositories/${id}/reports/security`, label: 'Security Audit', icon: ShieldCheck },
    { to: `/repositories/${id}/reports/quality`, label: 'Code Quality', icon: BarChart2 },
    { to: `/repositories/${id}/review`, label: 'AI Code Review', icon: Cpu },
    { to: `/repositories/${id}/executive-summary`, label: 'Executive Summary', icon: TrendingUp },
    { to: `/repositories/${id}/chat`, label: 'AI Code Chat', icon: MessageSquare },
  ];

  return (
    <div className="flex-1 flex overflow-hidden bg-zinc-950">
      {/* Sidebar Nav */}
      <aside className="w-56 flex flex-col border-r border-zinc-800/60 bg-zinc-900/10 shrink-0">
        {/* Back link */}
        <div className="p-4 border-b border-zinc-800/60">
          <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 font-medium transition-colors">
            <ChevronLeft size={13} /> Back to Dashboard
          </Link>
        </div>

        {/* Workspace Title Card */}
        <div className="p-4 border-b border-zinc-800/60 bg-zinc-900/30">
          <div className="flex items-center gap-2">
            <GitBranch size={15} className="text-violet-400 shrink-0" />
            <span className="text-sm font-bold text-zinc-200 truncate">{repo.name}</span>
          </div>
          <div className="text-[10px] text-zinc-500 font-mono truncate mt-1">{repo.github_url}</div>
          <div className="flex items-center gap-2 mt-3">
            <span className={cn(
              'badge text-[9px] px-1.5 py-0.5',
              repo.status === 'COMPLETE' ? 'badge-green' :
              repo.status === 'FAILED' ? 'badge-red' : 'badge-amber'
            )}>
              <span className={cn(
                'w-1 h-1 rounded-full',
                repo.status === 'COMPLETE' ? 'bg-emerald-400' :
                repo.status === 'FAILED' ? 'bg-red-400' : 'bg-amber-400 animate-pulse'
              )} />
              {repo.status}
            </span>
            <button
              onClick={() => refetch()}
              className="p-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Refresh repository metadata"
            >
              <RefreshCw size={10} />
            </button>
          </div>
        </div>

        {/* Tab Items */}
        <nav className="p-3 space-y-0.5 flex-1">
          {tabs.map((tab) => {
            const isActive = tab.exact 
              ? location.pathname === tab.to
              : location.pathname.startsWith(tab.to);

            return (
              <Link
                key={tab.to}
                to={tab.to}
                className={cn(
                  'flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150',
                  isActive
                    ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40'
                )}
              >
                <tab.icon size={14} />
                {tab.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Page Content Panel */}
      <main className="flex-1 overflow-hidden flex flex-col">
        <Outlet context={{ repo, refetch }} />
      </main>
    </div>
  );
}
