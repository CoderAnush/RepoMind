import { useOutletContext } from 'react-router-dom';
import type { Repository } from '../../types';
import {
  GitBranch, FileText, Code2, BookOpen, Terminal, Sparkles,
  ExternalLink, Calendar, RefreshCw
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

interface OutletContext {
  repo: Repository;
  refetch: () => void;
}

export default function RepoOverviewPage() {
  const { repo, refetch } = useOutletContext<OutletContext>();

  // If repo is still processing
  if (repo.status !== 'COMPLETE') {
    return (
      <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 flex flex-col justify-center items-center">
        <div className="max-w-md w-full glass-card p-8 border-zinc-800 bg-zinc-900/30 text-center">
          <RefreshCw size={36} className="text-violet-400 mx-auto animate-spin mb-4" />
          <h2 className="text-base font-bold text-zinc-200">Repository Analysis in Progress</h2>
          <p className="text-xs text-zinc-500 mt-2 leading-relaxed">
            We are currently cloning the repository and running semantic analysis. This page will update automatically.
          </p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <span className="badge-amber text-xs">
              <span className="status-dot-amber" />
              Status: {repo.status}
            </span>
            <button
              onClick={() => refetch()}
              className="btn-secondary py-1.5 px-3 text-xs bg-zinc-850 hover:bg-zinc-800"
            >
              Refresh Status
            </button>
          </div>
        </div>
      </div>
    );
  }

  const metadata = repo.metadata_info;
  const languagesPercentage = metadata?.languages_loc_percentage || {};
  
  // Transform languages data for Recharts Pie Chart
  const chartData = Object.entries(languagesPercentage).map(([name, val]) => ({
    name,
    value: parseFloat(val.toFixed(2))
  })).sort((a, b) => b.value - a.value);

  // Primary language
  const primaryLanguage = chartData[0]?.name || 'N/A';

  const COLORS = ['#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#EC4899'];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-zinc-950 relative">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
        <div>
          <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <Sparkles size={18} className="text-violet-400" />
            Repository Overview
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">Summary of analysis findings and structural metadata.</p>
        </div>
        
        <a
          href={repo.github_url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary self-start sm:self-center py-2 px-3 text-xs flex items-center gap-1.5 border border-zinc-850 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-300 font-medium"
        >
          View on GitHub <ExternalLink size={12} />
        </a>
      </div>

      {/* Overview Stat Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Indexed Files</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100">{metadata?.total_files || 0}</div>
            <div className="text-[10px] text-zinc-500 mt-1">Total workspace file count</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-zinc-800/80 flex items-center justify-center text-violet-400">
            <FileText size={16} />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Lines of Code</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100">{(metadata?.total_loc || 0).toLocaleString()}</div>
            <div className="text-[10px] text-zinc-500 mt-1">Source codebase volume</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-zinc-800/80 flex items-center justify-center text-cyan-400">
            <Code2 size={16} />
          </div>
        </div>

        {/* Metric 3 */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Primary Stack</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100 truncate max-w-[120px]">{primaryLanguage}</div>
            <div className="text-[10px] text-zinc-500 mt-1">Largest file index contributor</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-zinc-800/80 flex items-center justify-center text-emerald-400">
            <BookOpen size={16} />
          </div>
        </div>

        {/* Metric 4 */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Git Target Branch</span>
            <div className="text-2xl font-bold mt-1 text-zinc-100 font-mono">{repo.branch}</div>
            <div className="text-[10px] text-zinc-500 mt-1">Target branch selected</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-zinc-800/80 flex items-center justify-center text-amber-400">
            <GitBranch size={16} />
          </div>
        </div>
      </div>

      {/* Language Breakdown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Language Pie Chart */}
        <div className="lg:col-span-2 glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20">
          <h3 className="text-sm font-bold text-zinc-200 mb-4 flex items-center gap-1.5">
            <Terminal size={14} className="text-cyan-400" />
            Language Distribution
          </h3>

          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {chartData.length === 0 ? (
              <div className="text-zinc-500 text-xs py-10 w-full text-center">No language data.</div>
            ) : (
              <>
                <div className="w-full md:w-1/2 h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={70}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {chartData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#111827', borderColor: '#27272a', borderRadius: '8px' }}
                        itemStyle={{ fontSize: '11px' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="w-full md:w-1/2 space-y-3.5">
                  {chartData.map((item, idx) => (
                    <div key={item.name} className="space-y-1">
                      <div className="flex justify-between items-center text-xs">
                        <div className="flex items-center gap-2 font-medium text-zinc-300">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                          <span>{item.name}</span>
                        </div>
                        <span className="font-bold text-zinc-400">{item.value}%</span>
                      </div>
                      <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${item.value}%`,
                            backgroundColor: COLORS[idx % COLORS.length]
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Repository details metadata */}
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-zinc-200 mb-4 flex items-center gap-1.5">
              <Calendar size={14} className="text-violet-400" />
              Workspace Metadata
            </h3>

            <div className="space-y-4">
              <div>
                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">Workspace Owner</div>
                <div className="text-xs text-zinc-300 font-mono truncate mt-1">{repo.owner_id}</div>
              </div>

              <div>
                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">GitHub Remote Target</div>
                <div className="text-xs text-violet-400 font-mono truncate mt-1">
                  <a href={repo.github_url} target="_blank" rel="noopener noreferrer" className="hover:underline flex items-center gap-1 inline-flex">
                    {repo.github_url} <ExternalLink size={10} />
                  </a>
                </div>
              </div>

              <div>
                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">Clone Status</div>
                <div className="text-xs text-zinc-300 mt-1 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  Codebase completely parsed and indexed
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-zinc-800/80 pt-4 mt-6 flex justify-between items-center text-[10px] text-zinc-500 font-semibold">
            <span>RepoMind Analyzer v1</span>
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Online
            </span>
          </div>
        </div>
      </div>

      {/* Scanned files list preview */}
      {metadata?.file_list && metadata.file_list.length > 0 && (
        <div className="glass-card p-5 border border-zinc-850 rounded-xl bg-zinc-900/20">
          <h3 className="text-sm font-bold text-zinc-200 mb-3 flex items-center gap-1.5">
            <Terminal size={14} className="text-emerald-400" />
            Analyzed File Structure
          </h3>
          <div className="border border-zinc-800 bg-zinc-950 rounded-lg p-3 max-h-60 overflow-y-auto font-mono text-xs text-zinc-400 space-y-1.5">
            {metadata.file_list.map((file, idx) => (
              <div key={idx} className="flex items-center gap-2 hover:bg-zinc-900/50 py-0.5 px-1.5 rounded">
                <span className="text-zinc-600 font-sans select-none">{idx + 1}.</span>
                <span className="text-zinc-500">/</span>
                <span>{file}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
