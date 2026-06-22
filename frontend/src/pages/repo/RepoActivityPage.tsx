import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/api';
import {
  Activity, GitCommit, ShieldCheck, BookOpen,
  Bookmark, StickyNote, FileBarChart, Database, Cpu,
  Clock, RefreshCw
} from 'lucide-react';

const EVENT_CONFIG: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  REPOSITORY_INDEXED: {
    icon: <Database size={14} />,
    label: 'Repository Indexed',
    color: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
  },
  REVIEW_GENERATED: {
    icon: <ShieldCheck size={14} />,
    label: 'AI Code Review Generated',
    color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  },
  DOCUMENTATION_GENERATED: {
    icon: <BookOpen size={14} />,
    label: 'Documentation Generated',
    color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  },
  INSIGHT_SAVED: {
    icon: <Bookmark size={14} />,
    label: 'Insight Saved',
    color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  },
  NOTE_ADDED: {
    icon: <StickyNote size={14} />,
    label: 'Note Added',
    color: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
  },
  ARCHITECTURE_GENERATED: {
    icon: <Cpu size={14} />,
    label: 'Architecture Map Generated',
    color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  },
  REPORT_GENERATED: {
    icon: <FileBarChart size={14} />,
    label: 'Executive Report Generated',
    color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
  },
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'Just now';
}

export default function RepoActivityPage() {
  const { id } = useParams<{ id: string }>();

  const { data: events = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['activity', id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/collab/activity/${id}?limit=50`);
      return data;
    },
    enabled: !!id,
    refetchInterval: 30000,
  });

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Activity size={20} className="text-emerald-400" />
            Activity Timeline
          </h1>
          <p className="text-xs text-zinc-500 mt-1">
            Chronological feed of all engineering activity for this repository workspace.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 text-xs text-zinc-400 border border-zinc-800 hover:bg-zinc-800 px-3 py-2 rounded-xl transition-colors"
        >
          <RefreshCw size={13} className={isFetching ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="flex gap-4">
              <div className="skeleton w-8 h-8 rounded-full shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="skeleton h-4 w-48 rounded" />
                <div className="skeleton h-3 w-72 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="glass-card border border-zinc-850 rounded-2xl p-12 text-center">
          <Activity size={36} className="text-zinc-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-zinc-400">No activity yet</h3>
          <p className="text-xs text-zinc-600 mt-1">
            Activity will appear here as you index repositories, run reviews, and save insights.
          </p>
        </div>
      ) : (
        <div className="relative">
          {/* Timeline vertical line */}
          <div className="absolute left-4 top-4 bottom-4 w-px bg-zinc-800/70" />

          <div className="space-y-0">
            {events.map((ev: any, idx: number) => {
              const cfg = EVENT_CONFIG[ev.event_type] || {
                icon: <GitCommit size={14} />,
                label: ev.event_type.replace(/_/g, ' '),
                color: 'text-zinc-400 bg-zinc-800 border-zinc-700',
              };
              const isLast = idx === events.length - 1;

              return (
                <div key={ev.id} className="flex gap-4 relative">
                  {/* Icon bubble */}
                  <div className={`w-8 h-8 rounded-full border flex items-center justify-center shrink-0 z-10 ${cfg.color}`}>
                    {cfg.icon}
                  </div>

                  {/* Content card */}
                  <div className={`flex-1 pb-6 ${isLast ? '' : ''}`}>
                    <div className="glass-card border border-zinc-850 rounded-xl bg-zinc-900/10 p-4 hover:border-zinc-800 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <span className="text-sm font-bold text-zinc-200">{cfg.label}</span>
                        <span className="flex items-center gap-1 text-[10px] text-zinc-500">
                          <Clock size={10} />
                          {timeAgo(ev.created_at)} · {new Date(ev.created_at).toLocaleString('en-US', {
                            month: 'short', day: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                          })}
                        </span>
                      </div>
                      {ev.description && (
                        <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">{ev.description}</p>
                      )}
                      {ev.event_metadata && Object.keys(ev.event_metadata).length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {Object.entries(ev.event_metadata).map(([k, v]: any) => (
                            <span key={k} className="text-[9px] font-mono text-zinc-500 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded">
                              {k}: <span className="text-zinc-300">{String(v)}</span>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
