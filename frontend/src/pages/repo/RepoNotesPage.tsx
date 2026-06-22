import { useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../services/api';
import {
  StickyNote, Plus, Trash2, Pencil, Check, X,
  Clock
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const PLACEHOLDER_SUGGESTIONS = [
  'Authentication system needs refactoring — JWT secret should be in env vars',
  'Review database migration scripts before next deployment',
  'API rate limiting missing on /login endpoint',
  'Tech debt: replace deprecated `requests` calls with `httpx`',
];

export default function RepoNotesPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [draft, setDraft] = useState('');
  const [editId, setEditId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [previewMode, setPreviewMode] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { data: notes = [], isLoading } = useQuery({
    queryKey: ['notes', id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/collab/notes/${id}`);
      return data;
    },
    enabled: !!id,
  });

  const addMutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post(`/collab/notes/${id}`, { content: draft });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notes', id] });
      setDraft('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (noteId: string) => {
      await apiClient.delete(`/collab/notes/${noteId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notes', id] }),
  });

  const insertSuggestion = (s: string) => {
    setDraft(s);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <StickyNote size={20} className="text-amber-400" />
            Repository Notes
          </h1>
          <p className="text-xs text-zinc-500 mt-1">
            Attach observations, action items, and team notes to this workspace.
          </p>
        </div>
        <span className="text-[10px] text-zinc-500 bg-zinc-800/60 border border-zinc-800 px-2.5 py-1.5 rounded-lg font-mono">
          {notes.length} note{notes.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Compose Area */}
      <div className="glass-card rounded-2xl border border-zinc-800 bg-zinc-900/20 overflow-hidden">
        {/* Compose toolbar */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800/60 bg-zinc-900/40">
          <div className="flex items-center gap-2">
            <Pencil size={12} className="text-amber-400" />
            <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">New Note</span>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => setPreviewMode(false)}
              className={`px-2.5 py-1 text-[10px] font-bold rounded-md transition-colors ${!previewMode ? 'bg-zinc-700 text-zinc-200' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              Write
            </button>
            <button
              onClick={() => setPreviewMode(true)}
              className={`px-2.5 py-1 text-[10px] font-bold rounded-md transition-colors ${previewMode ? 'bg-zinc-700 text-zinc-200' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              Preview
            </button>
          </div>
        </div>

        {previewMode ? (
          <div className="p-4 min-h-[120px] markdown-body text-xs text-zinc-300 leading-relaxed">
            {draft ? <ReactMarkdown>{draft}</ReactMarkdown> : (
              <span className="text-zinc-600 italic">Nothing to preview yet...</span>
            )}
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={e => setDraft(e.target.value)}
            placeholder="Write a note in Markdown... e.g. **TODO**: Review auth service for SQL injection"
            rows={5}
            className="w-full bg-transparent border-0 px-4 py-3 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none font-mono resize-none"
          />
        )}

        <div className="flex items-center justify-between px-4 py-3 border-t border-zinc-800/60 bg-zinc-900/40">
          <div className="flex flex-wrap gap-1.5">
            {PLACEHOLDER_SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                onClick={() => insertSuggestion(s)}
                className="text-[9px] text-zinc-600 hover:text-zinc-300 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 px-2 py-0.5 rounded-full transition-colors truncate max-w-[200px]"
              >
                + {s.slice(0, 40)}...
              </button>
            ))}
          </div>
          <button
            onClick={() => addMutation.mutate()}
            disabled={!draft.trim() || addMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/90 hover:bg-amber-400 disabled:bg-zinc-800 disabled:text-zinc-600 text-zinc-900 font-bold text-xs rounded-lg transition-colors"
          >
            <Plus size={13} />
            {addMutation.isPending ? 'Saving...' : 'Add Note'}
          </button>
        </div>
      </div>

      {/* Notes List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map(i => <div key={i} className="skeleton h-28 w-full rounded-xl" />)}
        </div>
      ) : notes.length === 0 ? (
        <div className="glass-card border border-zinc-850 rounded-2xl p-12 text-center">
          <StickyNote size={36} className="text-zinc-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-zinc-400">No notes yet</h3>
          <p className="text-xs text-zinc-600 mt-1">Start capturing observations about this repository.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notes.map((note: any) => (
            <div
              key={note.id}
              className="glass-card border border-zinc-850 rounded-xl bg-zinc-900/10 overflow-hidden hover:border-amber-500/20 transition-colors group"
            >
              {editId === note.id ? (
                /* Edit mode */
                <div className="p-4 space-y-3">
                  <textarea
                    value={editContent}
                    onChange={e => setEditContent(e.target.value)}
                    rows={4}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-amber-500 font-mono resize-none"
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => setEditId(null)}
                      className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-200 px-3 py-1.5 rounded-lg border border-zinc-800 hover:bg-zinc-800"
                    >
                      <X size={12} /> Cancel
                    </button>
                    <button
                      onClick={() => {
                        // No patch endpoint needed for MVP — delete + re-add
                        deleteMutation.mutate(note.id);
                        setTimeout(() => {
                          apiClient.post(`/collab/notes/${id}`, { content: editContent })
                            .then(() => qc.invalidateQueries({ queryKey: ['notes', id] }));
                        }, 300);
                        setEditId(null);
                      }}
                      className="flex items-center gap-1 text-xs bg-amber-500/80 hover:bg-amber-400 text-zinc-900 font-bold px-3 py-1.5 rounded-lg"
                    >
                      <Check size={12} /> Save
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-4 flex gap-3 items-start">
                  <StickyNote size={16} className="text-amber-400/70 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="markdown-body text-xs text-zinc-300 leading-relaxed">
                      <ReactMarkdown>{note.content}</ReactMarkdown>
                    </div>
                    <div className="flex items-center gap-1.5 text-[10px] text-zinc-600 mt-2">
                      <Clock size={10} />
                      {new Date(note.created_at).toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric', year: 'numeric',
                        hour: '2-digit', minute: '2-digit'
                      })}
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    <button
                      onClick={() => { setEditId(note.id); setEditContent(note.content); }}
                      className="p-1.5 rounded-lg text-zinc-600 hover:text-amber-400 hover:bg-amber-500/10 transition-colors"
                    >
                      <Pencil size={12} />
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(note.id)}
                      className="p-1.5 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
