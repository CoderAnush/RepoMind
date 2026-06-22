import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../services/api';
import {
  Bookmark, Trash2, Sparkles, MessageSquare, GitBranch,
  Network, ShieldCheck, BookOpen, Plus, Search, Filter,
  ChevronDown, ChevronUp, Activity, Clock, Tag
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const INSIGHT_ICONS: Record<string, React.ReactNode> = {
  CHAT: <MessageSquare size={13} className="text-violet-400" />,
  TRACE: <GitBranch size={13} className="text-cyan-400" />,
  REVIEW: <ShieldCheck size={13} className="text-amber-400" />,
  ARCHITECTURE: <Network size={13} className="text-emerald-400" />,
  ONBOARDING: <BookOpen size={13} className="text-pink-400" />,
};

const INSIGHT_COLORS: Record<string, string> = {
  CHAT: 'border-violet-500/20 bg-violet-500/5 text-violet-300',
  TRACE: 'border-cyan-500/20 bg-cyan-500/5 text-cyan-300',
  REVIEW: 'border-amber-500/20 bg-amber-500/5 text-amber-300',
  ARCHITECTURE: 'border-emerald-500/20 bg-emerald-500/5 text-emerald-300',
  ONBOARDING: 'border-pink-500/20 bg-pink-500/5 text-pink-300',
};

export default function RepoInsightsPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  // Save dialog state
  const [showSave, setShowSave] = useState(false);
  const [saveTitle, setSaveTitle] = useState('');
  const [saveType, setSaveType] = useState('CHAT');
  const [saveContent, setSaveContent] = useState('');

  const { data: insights = [], isLoading } = useQuery({
    queryKey: ['insights', id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/collab/insights/${id}`);
      return data;
    },
    enabled: !!id,
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/collab/insights', {
        repository_id: id,
        title: saveTitle,
        insight_type: saveType,
        content: saveContent,
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['insights', id] });
      setShowSave(false);
      setSaveTitle('');
      setSaveContent('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (insightId: string) => {
      await apiClient.delete(`/collab/insights/${insightId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['insights', id] }),
  });

  const filtered = insights.filter((ins: any) => {
    const matchType = filter === 'ALL' || ins.insight_type === filter;
    const matchSearch = !search || ins.title.toLowerCase().includes(search.toLowerCase())
      || ins.content.toLowerCase().includes(search.toLowerCase());
    return matchType && matchSearch;
  });

  const types = ['ALL', 'CHAT', 'TRACE', 'REVIEW', 'ARCHITECTURE', 'ONBOARDING'];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Bookmark size={20} className="text-violet-400" />
            Saved Insights
          </h1>
          <p className="text-xs text-zinc-500 mt-1">
            Curated analyses, execution traces, and chat answers from your AI sessions.
          </p>
        </div>
        <button
          onClick={() => setShowSave(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold transition-colors"
        >
          <Plus size={14} /> Save New Insight
        </button>
      </div>

      {/* Save Dialog */}
      {showSave && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg glass-card rounded-2xl border border-zinc-800 p-6 space-y-4 bg-zinc-900">
            <h2 className="text-sm font-bold text-zinc-200 flex items-center gap-2">
              <Sparkles size={16} className="text-violet-400" /> Save Insight
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Title</label>
                <input
                  value={saveTitle}
                  onChange={e => setSaveTitle(e.target.value)}
                  placeholder="e.g. Authentication Flow Analysis"
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-violet-500"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Type</label>
                <select
                  value={saveType}
                  onChange={e => setSaveType(e.target.value)}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-violet-500"
                >
                  {['CHAT', 'TRACE', 'REVIEW', 'ARCHITECTURE', 'ONBOARDING'].map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Content (Markdown)</label>
                <textarea
                  value={saveContent}
                  onChange={e => setSaveContent(e.target.value)}
                  placeholder="Paste your AI answer, trace, or analysis here..."
                  rows={6}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-violet-500 resize-none font-mono"
                />
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowSave(false)}
                className="px-4 py-2 text-xs text-zinc-400 hover:text-zinc-200 rounded-lg border border-zinc-800 hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => saveMutation.mutate()}
                disabled={!saveTitle || !saveContent || saveMutation.isPending}
                className="px-4 py-2 text-xs bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-bold rounded-lg transition-colors"
              >
                {saveMutation.isPending ? 'Saving...' : 'Save Insight'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
        <div className="relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search insights..."
            className="bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-4 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-violet-500 w-48"
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {types.map(t => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-colors ${
                filter === t
                  ? 'bg-violet-500/10 border-violet-500/30 text-violet-300'
                  : 'border-zinc-800 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
              }`}
            >
              {t === 'ALL' ? (
                <span className="flex items-center gap-1"><Filter size={9} /> ALL</span>
              ) : (
                <span className="flex items-center gap-1">{INSIGHT_ICONS[t]} {t}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Insights Grid */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card border border-zinc-850 rounded-2xl p-12 text-center">
          <Bookmark size={36} className="text-zinc-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-zinc-400">No insights saved yet</h3>
          <p className="text-xs text-zinc-600 mt-1">
            Save AI chat answers, traces, or analysis results using the button above.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((ins: any) => {
            const isOpen = expandedId === ins.id;
            return (
              <div
                key={ins.id}
                className="glass-card border border-zinc-850 rounded-xl bg-zinc-900/10 overflow-hidden hover:border-zinc-800 transition-colors"
              >
                {/* Header Row */}
                <div
                  className="p-4 flex items-start gap-3 cursor-pointer select-none"
                  onClick={() => setExpandedId(isOpen ? null : ins.id)}
                >
                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg border text-[10px] font-bold shrink-0 ${INSIGHT_COLORS[ins.insight_type] || 'border-zinc-700 text-zinc-400'}`}>
                    {INSIGHT_ICONS[ins.insight_type]}
                    {ins.insight_type}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-zinc-200 truncate">{ins.title}</div>
                    <div className="text-[10px] text-zinc-500 mt-0.5 flex items-center gap-1.5">
                      <Clock size={10} />
                      {new Date(ins.created_at).toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={e => { e.stopPropagation(); deleteMutation.mutate(ins.id); }}
                      className="p-1.5 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 size={12} />
                    </button>
                    {isOpen ? <ChevronUp size={14} className="text-zinc-500" /> : <ChevronDown size={14} className="text-zinc-500" />}
                  </div>
                </div>

                {/* Expanded Content */}
                {isOpen && (
                  <div className="border-t border-zinc-800/60 bg-zinc-900/20 p-4">
                    <div className="markdown-body text-xs text-zinc-300 leading-relaxed max-h-80 overflow-y-auto">
                      <ReactMarkdown>{ins.content}</ReactMarkdown>
                    </div>

                    {/* Evidence mini-badge */}
                    {ins.evidence && (
                      <div className="mt-3 pt-3 border-t border-zinc-800/40 flex flex-wrap gap-2">
                        {ins.evidence.confidence_label && (
                          <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                            ins.evidence.confidence_label === 'HIGH'
                              ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10'
                              : ins.evidence.confidence_label === 'MEDIUM'
                              ? 'border-amber-500/30 text-amber-400 bg-amber-500/10'
                              : 'border-red-500/30 text-red-400 bg-red-500/10'
                          }`}>
                            <Activity size={9} className="inline mr-1" />
                            {ins.evidence.confidence_label} · {ins.evidence.confidence_score}%
                          </span>
                        )}
                        {ins.evidence.answer_type && (
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full border border-violet-500/20 text-violet-300 bg-violet-500/10">
                            <Tag size={9} className="inline mr-1" />
                            {ins.evidence.answer_type.replace(/_/g, ' ')}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
