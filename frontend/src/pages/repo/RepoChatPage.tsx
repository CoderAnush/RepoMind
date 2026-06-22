import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { chatService } from '../../services/endpoints';
import type { ChatMessage, ChatEvidence } from '../../types';
import {
  MessageSquare, Send, BookOpen, Sparkles,
  ChevronDown, ChevronUp, Copy, Check, FileCode,
  AlertCircle, ArrowUpRight, Shield, GitBranch,
  Layers, Target, BarChart3, Network, X, Activity
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

// ─── Evidence Panel Component ─────────────────────────────────────────────────
function EvidencePanel({ evidence, onClose }: { evidence: ChatEvidence; onClose: () => void }) {
  const confidenceColor =
    evidence.confidence_label === 'HIGH'
      ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
      : evidence.confidence_label === 'MEDIUM'
      ? 'text-amber-400 border-amber-500/30 bg-amber-500/10'
      : 'text-red-400 border-red-500/30 bg-red-500/10';

  const answerTypeLabel = (evidence.answer_type || 'GENERAL_QA')
    .replace(/_/g, ' ');

  return (
    <div className="absolute inset-y-0 right-0 w-80 z-20 border-l border-zinc-800/70 bg-zinc-950/95 backdrop-blur-xl flex flex-col overflow-hidden shadow-2xl">
      {/* Panel Header */}
      <div className="p-4 border-b border-zinc-800/60 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Shield size={13} className="text-violet-400" />
          <span className="text-xs font-bold text-zinc-200">Answer Evidence</span>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded-md text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
        >
          <X size={13} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">

        {/* Confidence Score */}
        <div className={`rounded-xl border p-3.5 ${confidenceColor}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Activity size={11} />
              Confidence
            </span>
            <span className="font-mono font-extrabold text-lg leading-none">
              {evidence.confidence_score}%
            </span>
          </div>
          <div className="w-full bg-zinc-800/60 h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                evidence.confidence_label === 'HIGH'
                  ? 'bg-emerald-400'
                  : evidence.confidence_label === 'MEDIUM'
                  ? 'bg-amber-400'
                  : 'bg-red-400'
              }`}
              style={{ width: `${evidence.confidence_score}%` }}
            />
          </div>
          <div className="mt-2 text-[10px] font-semibold opacity-80">
            {evidence.confidence_label} confidence
          </div>
        </div>

        {/* Answer Type */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-3.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5 mb-2">
            <Target size={11} />
            Answer Type
          </div>
          <span className="text-xs font-bold text-violet-300 bg-violet-500/10 border border-violet-500/20 px-2 py-1 rounded-lg">
            {answerTypeLabel}
          </span>
        </div>

        {/* Knowledge Graph Trace */}
        {evidence.graph_trace && evidence.graph_trace.path.length > 0 && (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-3.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5 mb-3">
              <Network size={11} />
              Graph Traversal
            </div>
            <div className="space-y-1">
              {evidence.graph_trace.path.slice(0, 8).map((node, i) => (
                <div key={i} className="flex flex-col items-start">
                  <span className="text-[11px] font-mono text-zinc-200 bg-zinc-800/60 border border-zinc-700/50 px-2 py-0.5 rounded-md truncate max-w-full">
                    {node}
                  </span>
                  {i < Math.min(evidence.graph_trace.path.length - 1, 7) && (
                    <span className="text-zinc-600 text-xs ml-2 leading-none">↓</span>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-zinc-800/50 grid grid-cols-2 gap-2 text-[10px]">
              <div className="text-zinc-500">
                Visited Nodes
                <div className="font-bold text-zinc-200 font-mono text-sm">{evidence.graph_trace.visited_nodes}</div>
              </div>
              <div className="text-zinc-500">
                Traversal Depth
                <div className="font-bold text-zinc-200 font-mono text-sm">{evidence.graph_trace.depth}</div>
              </div>
            </div>
          </div>
        )}

        {/* Retrieved Files */}
        {evidence.retrieved_files && evidence.retrieved_files.length > 0 && (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-3.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5 mb-2.5">
              <Layers size={11} />
              Retrieved Files ({evidence.retrieved_files.length})
            </div>
            <div className="space-y-1.5">
              {evidence.retrieved_files.map((f, i) => (
                <div key={i} className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-300">
                  <FileCode size={10} className="text-violet-400 shrink-0" />
                  <span className="truncate">{f}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Retrieved Chunks with Scores */}
        {evidence.retrieved_chunks && evidence.retrieved_chunks.length > 0 && (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-3.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5 mb-3">
              <BarChart3 size={11} />
              Retrieval Scores
            </div>
            <div className="space-y-2.5">
              {evidence.retrieved_chunks.map((chunk, i) => {
                const score = chunk.similarity_score ?? 0.85;
                const pct = Math.round(score * 100);
                const barColor =
                  pct >= 85 ? 'bg-emerald-500' : pct >= 70 ? 'bg-amber-500' : 'bg-red-500';
                return (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-mono text-zinc-400 truncate max-w-[65%]">
                        {chunk.symbol || chunk.file_path?.split(/[\\/]/).pop() || `chunk_${i}`}
                      </span>
                      <span className="font-mono font-bold text-zinc-200">{score.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-zinc-800 h-1 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${barColor}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Source Attestation */}
        <div className="rounded-xl border border-zinc-800/40 bg-violet-950/10 p-3 text-[10px] text-zinc-500 leading-relaxed">
          <GitBranch size={11} className="text-violet-400 inline mr-1.5" />
          This answer was synthesized from <strong className="text-zinc-300">{evidence.retrieved_chunks?.length || 0}</strong> indexed code chunks across <strong className="text-zinc-300">{evidence.retrieved_files?.length || 0}</strong> files using RAG + Knowledge Graph traversal.
        </div>
      </div>
    </div>
  );
}

// ─── Main Chat Page ────────────────────────────────────────────────────────────
export default function RepoChatPage() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [openCitationsIndex, setOpenCitationsIndex] = useState<Record<number, boolean>>({});
  const [evidencePanelMsg, setEvidencePanelMsg] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const suggestions = [
    { text: 'Explain authentication flow', query: 'Explain the authentication flow, schemas, and supabase proxy routes.' },
    { text: 'Show database schema', query: 'Show the database schemas, SQLAlchemy models, and table setup.' },
    { text: 'Generate onboarding guide', query: 'Generate a developer onboarding guide with install and testing steps.' },
    { text: 'Find security issues', query: 'Identify security findings, exposed credentials, and audit details.' },
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (msgText: string) => {
    if (!msgText.trim() || loading) return;
    setError(null);
    setLoading(true);
    setEvidencePanelMsg(null);

    const userMsg: ChatMessage = {
      role: 'user',
      message: msgText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');

    try {
      const res = await chatService.send({
        repository_id: id!,
        message: msgText,
        conversation_id: sessionId,
        ...({ session_id: sessionId } as any)
      } as any);

      const receivedSessionId = res.conversation_id || (res as any).session_id;
      if (receivedSessionId && !sessionId) {
        setSessionId(receivedSessionId);
      }

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        message: res.answer,
        references: res.references,
        evidence: (res as any).evidence,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to query the repository index. Ensure vector database is reachable.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputMessage);
    }
  };

  const handleCopyCode = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const toggleCitations = (idx: number) => {
    setOpenCitationsIndex(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const toggleEvidencePanel = (idx: number) => {
    setEvidencePanelMsg(prev => (prev === idx ? null : idx));
  };

  const renderers = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <div className="relative group my-3">
          <div className="absolute right-3 top-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
            <button
              onClick={() => navigator.clipboard.writeText(String(children).replace(/\n$/, ''))}
              className="p-1 rounded bg-zinc-800 border border-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              <Copy size={10} />
            </button>
          </div>
          <SyntaxHighlighter
            {...props}
            style={tomorrow}
            language={match[1]}
            PreTag="div"
            className="rounded-lg border border-zinc-800/80 !m-0 !bg-zinc-900/50 text-xs"
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code className="font-mono bg-zinc-800 text-violet-300 px-1 py-0.5 rounded text-[0.85em]" {...props}>
          {children}
        </code>
      );
    }
  };

  const activeEvidence =
    evidencePanelMsg !== null ? messages[evidencePanelMsg]?.evidence : undefined;

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-zinc-950 relative">

      {/* Scope Header */}
      <div className="p-4 border-b border-zinc-800/60 bg-zinc-900/10 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <MessageSquare size={16} className="text-violet-400" />
          <span className="text-xs font-bold text-zinc-200">Repository Intelligence Chat</span>
        </div>
        <div className="text-[10px] text-zinc-500 font-semibold flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_4px_rgba(52,211,153,0.5)]" />
          Scoped to workspace vectors
        </div>
      </div>

      {/* Main area: messages + optional evidence sidebar */}
      <div className="flex-1 flex overflow-hidden relative">

        {/* Messages Scroll Area */}
        <div className={`flex-1 overflow-y-auto p-4 md:p-6 space-y-6 transition-all duration-300 ${activeEvidence ? 'mr-80' : ''}`}>
          {messages.length === 0 ? (
            <div className="max-w-xl mx-auto py-16 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 mb-6">
                <Sparkles size={22} className="animate-pulse" />
              </div>
              <h2 className="text-base font-bold text-zinc-200">Semantic Code Assistant</h2>
              <p className="text-xs text-zinc-500 mt-2 max-w-sm leading-relaxed">
                Ask questions about classes, execution paths, dependencies, and configuration. Every answer includes <span className="text-violet-400 font-semibold">evidence traces</span> and a <span className="text-violet-400 font-semibold">confidence score</span>.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-10 w-full">
                {suggestions.map((sug, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(sug.query)}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-zinc-850 hover:border-violet-500/30 bg-zinc-900/10 hover:bg-violet-500/5 text-left text-xs text-zinc-400 hover:text-zinc-200 transition-all group"
                  >
                    <span>{sug.text}</span>
                    <ArrowUpRight size={13} className="text-zinc-600 group-hover:text-violet-400 transition-colors shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg, index) => {
                const isUser = msg.role === 'user';
                const hasEvidence = !isUser && !!msg.evidence;
                const isEvidenceOpen = evidencePanelMsg === index;
                const ev = msg.evidence;

                return (
                  <div key={index} className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    {/* Avatar */}
                    {!isUser && (
                      <div className="w-7 h-7 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 shrink-0 text-[10px]">
                        <Sparkles size={13} />
                      </div>
                    )}

                    {/* Bubble content */}
                    <div className={`max-w-[85%] rounded-xl p-4 border ${
                      isUser
                        ? 'bg-zinc-800/80 border-zinc-700/60 text-zinc-100'
                        : 'bg-zinc-900/40 border-zinc-850/80 text-zinc-200'
                    }`}>
                      {/* Message body */}
                      <div className="markdown-body text-xs">
                        <ReactMarkdown components={renderers}>
                          {msg.message}
                        </ReactMarkdown>
                      </div>

                      {/* Evidence + Citations Footer */}
                      {!isUser && (
                        <div className="border-t border-zinc-800/60 pt-3 mt-3 space-y-2.5">

                          {/* Evidence Pill Row */}
                          {hasEvidence && ev && (
                            <div className="flex flex-wrap items-center gap-2">
                              {/* Confidence badge */}
                              <span className={`inline-flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full border ${
                                ev.confidence_label === 'HIGH'
                                  ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
                                  : ev.confidence_label === 'MEDIUM'
                                  ? 'text-amber-400 border-amber-500/30 bg-amber-500/10'
                                  : 'text-red-400 border-red-500/30 bg-red-500/10'
                              }`}>
                                <Activity size={9} />
                                {ev.confidence_label} · {ev.confidence_score}%
                              </span>

                              {/* Answer type badge */}
                              <span className="inline-flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full border border-violet-500/20 bg-violet-500/10 text-violet-300">
                                <Target size={9} />
                                {(ev.answer_type || 'GENERAL_QA').replace(/_/g, ' ')}
                              </span>

                              {/* Graph trace pill */}
                              {ev.graph_trace && ev.graph_trace.visited_nodes > 0 && (
                                <span className="inline-flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full border border-cyan-500/20 bg-cyan-500/10 text-cyan-300">
                                  <Network size={9} />
                                  {ev.graph_trace.visited_nodes} nodes · depth {ev.graph_trace.depth}
                                </span>
                              )}

                              {/* Evidence panel toggle */}
                              <button
                                onClick={() => toggleEvidencePanel(index)}
                                className={`inline-flex items-center gap-1 text-[9px] font-bold px-2 py-0.5 rounded-full border transition-colors ${
                                  isEvidenceOpen
                                    ? 'border-violet-500/40 bg-violet-500/20 text-violet-300'
                                    : 'border-zinc-700 bg-zinc-800/50 text-zinc-400 hover:text-zinc-200'
                                }`}
                              >
                                <Shield size={9} />
                                {isEvidenceOpen ? 'Hide Evidence' : 'View Evidence'}
                              </button>
                            </div>
                          )}

                          {/* Citations Accordion */}
                          {msg.references && msg.references.length > 0 && (
                            <div>
                              <button
                                onClick={() => toggleCitations(index)}
                                className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-500 hover:text-zinc-300 transition-colors focus:outline-none"
                              >
                                <BookOpen size={11} />
                                <span>Sources Referenced ({msg.references.length})</span>
                                {openCitationsIndex[index] ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                              </button>

                              {openCitationsIndex[index] && (
                                <div className="space-y-2.5 mt-2.5">
                                  {msg.references.map((ref, rIdx) => (
                                    <div key={rIdx} className="bg-zinc-950 border border-zinc-850 p-2.5 rounded-lg">
                                      <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono mb-1.5 pb-1 border-b border-zinc-900">
                                        <span className="flex items-center gap-1">
                                          <FileCode size={11} className="text-violet-400" />
                                          {ref.file_path}
                                        </span>
                                        <button
                                          onClick={() => handleCopyCode(ref.snippet, rIdx)}
                                          className="hover:text-zinc-300 flex items-center gap-0.5"
                                        >
                                          {copiedIndex === rIdx ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
                                        </button>
                                      </div>
                                      <pre className="font-mono text-[9px] text-zinc-400 overflow-x-auto bg-transparent p-0 m-0 leading-normal">
                                        <code>{ref.snippet}</code>
                                      </pre>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Error alert */}
              {error && (
                <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Loading placeholder */}
              {loading && (
                <div className="flex gap-4">
                  <div className="w-7 h-7 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 shrink-0 animate-pulse">
                    <Sparkles size={13} className="animate-spin" />
                  </div>
                  <div className="bg-zinc-900/30 border border-zinc-850 p-4 rounded-xl max-w-[85%] flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce" />
                    <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce [animation-delay:0.2s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce [animation-delay:0.4s]" />
                    <span className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider pl-2 animate-pulse">Searching vectors & graph...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Evidence Side Panel (floating over the right side) */}
        {activeEvidence && (
          <EvidencePanel
            evidence={activeEvidence}
            onClose={() => setEvidencePanelMsg(null)}
          />
        )}
      </div>

      {/* Input panel */}
      <div className="p-4 border-t border-zinc-800/60 bg-zinc-900/10 shrink-0">
        <div className="max-w-3xl mx-auto relative glass bg-zinc-900/60 border-zinc-800/80 rounded-xl p-2.5 flex items-end gap-2 shadow-2xl">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask RepoMind about code modules, database relations..."
            rows={1}
            disabled={loading}
            className="flex-1 bg-transparent border-0 resize-none font-sans text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-0 max-h-32 min-h-[24px] py-1 pl-2.5"
          />
          <button
            onClick={() => handleSendMessage(inputMessage)}
            disabled={!inputMessage.trim() || loading}
            className="w-8 h-8 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-800 text-white disabled:text-zinc-600 flex items-center justify-center transition-colors focus:outline-none"
          >
            <Send size={13} />
          </button>
        </div>
        <div className="max-w-3xl mx-auto text-[9px] text-zinc-600 text-center mt-1.5 font-medium">
          Press Enter to query · Shift + Enter for line breaks · Click <Shield size={9} className="inline text-violet-500" /> to audit evidence
        </div>
      </div>
    </div>
  );
}
