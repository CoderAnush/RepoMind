import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Sparkles, LayoutDashboard, GitBranch, LogOut,
  Plus, ChevronRight, Zap
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { repoService } from '../services/endpoints';
import { cn } from '../utils/cn';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/repositories', icon: GitBranch, label: 'Repositories' },
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const { data: repos = [] } = useQuery({
    queryKey: ['repositories'],
    queryFn: repoService.list,
    staleTime: 30_000,
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex flex-col border-r border-zinc-800/60 bg-zinc-950 shrink-0">
        {/* Logo */}
        <div className="p-5 border-b border-zinc-800/60">
          <Link to="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Sparkles size={16} className="text-white" />
            </div>
            <div>
              <span className="text-sm font-bold text-zinc-100">RepoMind</span>
              <div className="text-[10px] text-zinc-500 font-medium leading-tight">AI Intelligence</div>
            </div>
          </Link>
        </div>

        {/* Main nav */}
        <nav className="p-3 space-y-0.5">
          {navItems.map(({ to, icon: Icon, label }) => {
            const isActive = location.pathname === to || location.pathname.startsWith(to + '/');
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60'
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Recent Repositories */}
        {repos.length > 0 && (
          <div className="px-3 py-2">
            <div className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider px-3 py-2">
              Recent Repos
            </div>
            <div className="space-y-0.5">
              {repos.slice(0, 5).map((repo) => {
                const isActive = location.pathname.startsWith(`/repositories/${repo.id}`);
                return (
                  <Link
                    key={repo.id}
                    to={`/repositories/${repo.id}`}
                    className={cn(
                      'flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-all duration-150 group',
                      isActive
                        ? 'bg-zinc-800 text-zinc-200'
                        : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40'
                    )}
                  >
                    <div className={cn(
                      'w-1.5 h-1.5 rounded-full shrink-0',
                      repo.status === 'COMPLETE' ? 'bg-emerald-400' :
                      repo.status === 'FAILED' ? 'bg-red-400' : 'bg-amber-400 animate-pulse'
                    )} />
                    <span className="truncate font-medium">{repo.name}</span>
                    <ChevronRight size={10} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {/* New repo CTA */}
        <div className="px-3 mt-2">
          <Link
            to="/repositories/new"
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium text-zinc-500 hover:text-violet-400 hover:bg-violet-500/5 border border-dashed border-zinc-800 hover:border-violet-500/30 transition-all duration-200"
          >
            <Plus size={13} />
            Analyze Repository
          </Link>
        </div>

        {/* Bottom */}
        <div className="mt-auto p-3 border-t border-zinc-800/60">
          {/* Status badge */}
          <div className="flex items-center gap-2 px-3 py-2 mb-1">
            <Zap size={12} className="text-emerald-400" />
            <span className="text-[10px] text-zinc-500 font-medium">API Connected</span>
          </div>

          {/* User */}
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
              {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-zinc-300 truncate">
                {user?.full_name || 'User'}
              </div>
              <div className="text-[10px] text-zinc-500 truncate">{user?.email}</div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1 rounded text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Sign out"
            >
              <LogOut size={13} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden flex flex-col">
        {children}
      </main>
    </div>
  );
}
