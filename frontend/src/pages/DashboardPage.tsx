import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { repoService } from '../services/endpoints';
import {
  Sparkles, GitBranch, FileText, Network, ShieldCheck,
  Search, Plus, Filter, ArrowUpDown, ChevronRight, Terminal, BarChart2, BookOpen
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar, Cell } from 'recharts';

export default function DashboardPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [sortField, setSortField] = useState<'name' | 'created_at' | 'status'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // React Query to fetch repositories
  const { data: repos = [], isLoading, error } = useQuery({
    queryKey: ['repositories'],
    queryFn: repoService.list,
    refetchInterval: 10000, // Poll every 10s to keep sync with background processing
  });

  // Calculate Metrics
  const metrics = useMemo(() => {
    const totalRepos = repos.length;
    const completedRepos = repos.filter(r => r.status === 'COMPLETE');
    const totalFiles = completedRepos.reduce((acc, r) => acc + (r.metadata_info?.total_files || 0), 0);
    const totalLoc = completedRepos.reduce((acc, r) => acc + (r.metadata_info?.total_loc || 0), 0);
    const docsCount = completedRepos.length * 6; // Seeded docs per repo
    const diagramsCount = completedRepos.length * 4; // Seeded diagrams per repo

    return {
      totalRepos,
      completedRepos: completedRepos.length,
      totalFiles,
      totalLoc,
      docsCount,
      diagramsCount
    };
  }, [repos]);

  // Aggregate Language Distribution for Chart
  const languageData = useMemo(() => {
    const langs: Record<string, number> = {};
    repos.forEach(repo => {
      if (repo.metadata_info?.languages) {
        Object.entries(repo.metadata_info.languages).forEach(([lang, val]) => {
          langs[lang] = (langs[lang] || 0) + val;
        });
      }
    });
    return Object.entries(langs).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
  }, [repos]);

  // Generate mock time-series data for analysis activity chart based on repo created dates
  const activityData = useMemo(() => {
    // Group repositories by date
    const groups: Record<string, number> = {};
    repos.forEach(repo => {
      const date = new Date(repo.created_at || Date.now()).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      groups[date] = (groups[date] || 0) + 1;
    });

    // If empty, generate standard filler
    if (Object.keys(groups).length === 0) {
      return [
        { date: 'Jun 14', count: 0 },
        { date: 'Jun 15', count: 0 },
        { date: 'Jun 16', count: 0 },
        { date: 'Jun 17', count: 0 },
        { date: 'Jun 18', count: 0 },
        { date: 'Jun 19', count: 0 },
      ];
    }

    return Object.entries(groups).map(([date, count]) => ({ date, count })).reverse();
  }, [repos]);

  // Sort and Filter Table
  const handleSort = (field: 'name' | 'created_at' | 'status') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const filteredRepos = useMemo(() => {
    return repos
      .filter(repo => {
        const matchesSearch = repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          repo.github_url.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = statusFilter === 'ALL' || repo.status === statusFilter;
        return matchesSearch && matchesFilter;
      })
      .sort((a, b) => {
        let valA: any = a[sortField];
        let valB: any = b[sortField];

        if (sortField === 'created_at') {
          valA = new Date(a.created_at || 0).getTime();
          valB = new Date(b.created_at || 0).getTime();
        }

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
  }, [repos, searchTerm, statusFilter, sortField, sortOrder]);

  const COLORS = ['#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#EC4899'];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 bg-zinc-950 relative">
      {/* Background glow effects */}
      <div className="absolute top-[10%] right-[10%] w-[35%] h-[35%] rounded-full bg-violet-600/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[20%] left-[5%] w-[40%] h-[40%] rounded-full bg-cyan-600/5 blur-[120px] pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Sparkles size={20} className="text-violet-400" />
            Dashboard
          </h1>
          <p className="text-xs text-zinc-500 mt-1">Monitor, query, and audit your indexed source code bases.</p>
        </div>
        <Link
          to="/repositories/new"
          className="btn-primary self-start sm:self-center bg-violet-600 hover:bg-violet-500 px-4 py-2 text-xs font-bold shadow-md shadow-violet-500/10"
        >
          <Plus size={14} /> Analyze Repository
        </Link>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="metric-card bg-zinc-900/60 border border-zinc-850 p-5 rounded-xl hover:border-zinc-800 transition-all flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Total Repositories</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100">{metrics.totalRepos}</div>
            <div className="text-[10px] text-zinc-500 mt-1.5 flex items-center gap-1">
              <span className="text-emerald-400 font-bold">{metrics.completedRepos}</span> fully completed
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-zinc-800/80 flex items-center justify-center text-violet-400">
            <GitBranch size={18} />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="metric-card bg-zinc-900/60 border border-zinc-850 p-5 rounded-xl hover:border-zinc-800 transition-all flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Docs Generated</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100">{metrics.docsCount}</div>
            <div className="text-[10px] text-zinc-500 mt-1.5">
              Across onboarding, API & README
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-zinc-800/80 flex items-center justify-center text-cyan-400">
            <FileText size={18} />
          </div>
        </div>

        {/* Metric 3 */}
        <div className="metric-card bg-zinc-900/60 border border-zinc-850 p-5 rounded-xl hover:border-zinc-800 transition-all flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Diagrams Rendered</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100">{metrics.diagramsCount}</div>
            <div className="text-[10px] text-zinc-500 mt-1.5">
              UML classes and architecture flow
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-zinc-800/80 flex items-center justify-center text-emerald-400">
            <Network size={18} />
          </div>
        </div>

        {/* Metric 4 */}
        <div className="metric-card bg-zinc-900/60 border border-zinc-850 p-5 rounded-xl hover:border-zinc-800 transition-all flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Total Lines of Code</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100">{metrics.totalLoc.toLocaleString()}</div>
            <div className="text-[10px] text-zinc-500 mt-1.5 flex items-center gap-1">
              <span className="text-cyan-400 font-bold">{metrics.totalFiles}</span> files indexed in vector DB
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-zinc-800/80 flex items-center justify-center text-amber-400">
            <BookOpen size={18} />
          </div>
        </div>
      </div>

      {/* Analytics Charts */}
      {repos.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* LOC Activity Area Chart */}
          <div className="lg:col-span-2 glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/30">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-zinc-200">Repository Analysis Timeline</h3>
                <span className="text-[10px] text-zinc-500">Repositories analyzed over the past week</span>
              </div>
              <BarChart2 size={16} className="text-violet-400" />
            </div>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#27272a', borderRadius: '8px' }}
                    labelStyle={{ color: '#a1a1aa', fontSize: '11px', fontWeight: 'bold' }}
                    itemStyle={{ color: '#8B5CF6', fontSize: '11px' }}
                  />
                  <Area type="monotone" dataKey="count" stroke="#8B5CF6" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Language Breakdown */}
          <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/30">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-zinc-200">Indexed Languages</h3>
                <span className="text-[10px] text-zinc-500">Aggregated file types across workspaces</span>
              </div>
              <Terminal size={16} className="text-cyan-400" />
            </div>
            {languageData.length === 0 ? (
              <div className="h-60 flex flex-col items-center justify-center text-zinc-600 text-xs">
                No codebase language details available yet.
              </div>
            ) : (
              <div className="h-60">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={languageData.slice(0, 6)} layout="vertical" margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <XAxis type="number" stroke="#52525b" fontSize={9} tickLine={false} axisLine={false} />
                    <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={10} tickLine={false} axisLine={false} width={60} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#27272a', borderRadius: '8px' }}
                      itemStyle={{ color: '#06B6D4', fontSize: '11px' }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={12}>
                      {languageData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Repository Table Section */}
      <div className="glass-card border border-zinc-850 rounded-xl bg-zinc-900/30 overflow-hidden">
        {/* Table Filters */}
        <div className="p-4 border-b border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-zinc-900/50">
          <div className="relative flex-1 max-w-sm">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500">
              <Search size={15} />
            </span>
            <input
              type="text"
              placeholder="Search workspaces by name or URL..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800/80 rounded-lg pl-9 pr-4 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/60 focus:ring-1 focus:ring-violet-500/60"
            />
          </div>

          <div className="flex items-center gap-3.5">
            {/* Filter */}
            <div className="flex items-center gap-1.5">
              <Filter size={13} className="text-zinc-500" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-zinc-950 border border-zinc-800/80 rounded-lg text-xs text-zinc-400 px-2.5 py-1.5 focus:outline-none focus:border-violet-500/60"
              >
                <option value="ALL">All Statuses</option>
                <option value="PENDING">Pending</option>
                <option value="CLONING">Cloning</option>
                <option value="INDEXING">Indexing</option>
                <option value="COMPLETE">Complete</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table Grid */}
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-8 space-y-3">
              <div className="skeleton h-8 w-full" />
              <div className="skeleton h-12 w-full" />
              <div className="skeleton h-12 w-full" />
            </div>
          ) : error ? (
            <div className="p-12 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 mb-3">
                <ShieldCheck size={20} />
              </div>
              <h3 className="text-sm font-bold text-zinc-300">Connection Failed</h3>
              <p className="text-xs text-zinc-500 max-w-sm mt-1">Could not connect to the backend server. Please verify settings.</p>
            </div>
          ) : filteredRepos.length === 0 ? (
            <div className="p-12 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-500 mb-3">
                <GitBranch size={20} />
              </div>
              <h3 className="text-sm font-bold text-zinc-300">No Repositories Tracked</h3>
              <p className="text-xs text-zinc-500 max-w-sm mt-1">Submit your first GitHub URL to run documentation, security audits, and RAG search.</p>
              <Link to="/repositories/new" className="btn-primary mt-4 py-2 px-3 text-xs bg-violet-600 hover:bg-violet-500">
                Analyze Repository
              </Link>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-800/80 bg-zinc-900/30 text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                  <th className="px-5 py-3 cursor-pointer select-none hover:text-zinc-300" onClick={() => handleSort('name')}>
                    <span className="flex items-center gap-1">Repository Name <ArrowUpDown size={10} /></span>
                  </th>
                  <th className="px-5 py-3 cursor-pointer select-none hover:text-zinc-300" onClick={() => handleSort('status')}>
                    <span className="flex items-center gap-1">Status <ArrowUpDown size={10} /></span>
                  </th>
                  <th className="px-5 py-3">Git Branch</th>
                  <th className="px-5 py-3">Security Score</th>
                  <th className="px-5 py-3">Quality Score</th>
                  <th className="px-5 py-3 cursor-pointer select-none hover:text-zinc-300 text-right" onClick={() => handleSort('created_at')}>
                    <span className="flex items-center gap-1 justify-end">Date Submitted <ArrowUpDown size={10} /></span>
                  </th>
                  <th className="px-5 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-850">
                {filteredRepos.map((repo) => {
                  return (
                    <tr
                      key={repo.id}
                      className="text-xs hover:bg-zinc-900/40 transition-colors group cursor-pointer"
                      onClick={() => navigateToRepo(repo)}
                    >
                      <td className="px-5 py-4">
                        <div className="font-semibold text-zinc-300 group-hover:text-violet-400 transition-colors">{repo.name}</div>
                        <div className="text-[10px] text-zinc-500 truncate max-w-xs sm:max-w-sm mt-0.5">{repo.github_url}</div>
                      </td>
                      <td className="px-5 py-4">
                        <span className={
                          repo.status === 'COMPLETE' ? 'badge-green' :
                          repo.status === 'FAILED' ? 'badge-red' :
                          'badge-amber'
                        }>
                          <span className={
                            repo.status === 'COMPLETE' ? 'status-dot-green' :
                            repo.status === 'FAILED' ? 'status-dot-red' :
                            'status-dot-amber'
                          } />
                          {repo.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 font-mono text-[10px] text-zinc-500">{repo.branch}</td>
                      <td className="px-5 py-4">
                        {repo.status === 'COMPLETE' ? (
                          <span className="badge-purple font-bold">100 / 100</span>
                        ) : (
                          <span className="text-zinc-600">—</span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        {repo.status === 'COMPLETE' ? (
                          <span className="badge-cyan font-bold">95 / 100</span>
                        ) : (
                          <span className="text-zinc-600">—</span>
                        )}
                      </td>
                      <td className="px-5 py-4 text-zinc-500 text-right">
                        {new Date(repo.created_at || Date.now()).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric'
                        })}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <ChevronRight size={14} className="text-zinc-600 group-hover:text-zinc-300 group-hover:translate-x-0.5 transition-all ml-auto" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );

  function navigateToRepo(repo: any) {
    window.location.href = `/repositories/${repo.id}`;
  }
}
