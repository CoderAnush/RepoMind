import { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { docsService } from '../../services/endpoints';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
  FileText, Search, Copy, Check, Calendar,
  BookOpen, ShieldAlert, Sparkles
} from 'lucide-react';

export default function RepoDocsPage() {
  const { id } = useParams<{ id: string }>();
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [copied, setCopied] = useState(false);

  // Fetch docs from API
  const { data: docs = [], isLoading, error } = useQuery({
    queryKey: ['docs', id],
    queryFn: () => docsService.list(id!),
    enabled: !!id,
  });

  // Select first document automatically once loaded
  useMemo(() => {
    if (docs.length > 0 && !selectedDocId) {
      setSelectedDocId(docs[0].id);
    }
  }, [docs, selectedDocId]);

  const activeDoc = useMemo(() => {
    return docs.find(doc => doc.id === selectedDocId) || null;
  }, [docs, selectedDocId]);

  // Search within documentation titles/content
  const filteredDocs = useMemo(() => {
    return docs.filter(doc =>
      doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.content.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [docs, searchTerm]);

  const handleCopy = async () => {
    if (!activeDoc) return;
    try {
      await navigator.clipboard.writeText(activeDoc.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  // Custom components for Markdown rendering (Syntax Highlighting + Tables)
  const renderers = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <div className="relative group my-4">
          <div className="absolute right-3 top-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
            <button
              onClick={() => navigator.clipboard.writeText(String(children).replace(/\n$/, ''))}
              className="p-1.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Copy snippet"
            >
              <Copy size={11} />
            </button>
          </div>
          <SyntaxHighlighter
            {...props}
            style={tomorrow}
            language={match[1]}
            PreTag="div"
            className="rounded-xl border border-zinc-800/80 !m-0 !bg-zinc-900/60"
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 bg-zinc-950 flex p-6 gap-6">
        {/* Sidebar skeleton */}
        <div className="w-64 border-r border-zinc-850 pr-6 space-y-4">
          <div className="skeleton h-8 w-full" />
          <div className="skeleton h-12 w-full" />
          <div className="skeleton h-12 w-full" />
          <div className="skeleton h-12 w-full" />
        </div>
        {/* Content skeleton */}
        <div className="flex-1 space-y-6">
          <div className="skeleton h-10 w-2/3" />
          <div className="skeleton h-6 w-1/4" />
          <div className="skeleton h-80 w-full" />
        </div>
      </div>
    );
  }

  if (error || docs.length === 0) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center p-6 text-center">
        <div className="max-w-md glass-card p-8 border-zinc-850 bg-zinc-900/10">
          <ShieldAlert size={32} className="text-zinc-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-zinc-200 font-sans">No Documentation Generated</h2>
          <p className="text-xs text-zinc-500 mt-2">
            No documentation has been generated yet for this workspace. Wait for analysis completion or click analyze.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex overflow-hidden bg-zinc-950">
      {/* Sidebar List of Documents */}
      <aside className="w-64 border-r border-zinc-800/60 flex flex-col bg-zinc-900/10 shrink-0">
        <div className="p-4 border-b border-zinc-800/60">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">
              <Search size={14} />
            </span>
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/60"
            />
          </div>
        </div>

        <nav className="p-3 space-y-0.5 overflow-y-auto flex-1">
          {filteredDocs.map((doc) => {
            const isSelected = doc.id === selectedDocId;
            return (
              <button
                key={doc.id}
                onClick={() => setSelectedDocId(doc.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-xs font-semibold transition-all duration-150 ${
                  isSelected
                    ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                }`}
              >
                <FileText size={14} className={isSelected ? 'text-violet-400' : 'text-zinc-500'} />
                <span className="truncate">{doc.title}</span>
              </button>
            );
          })}
          {filteredDocs.length === 0 && (
            <div className="text-[10px] text-zinc-600 text-center py-6">No matching documents found.</div>
          )}
        </nav>
      </aside>

      {/* Main Document Content Area */}
      <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 relative flex flex-col">
        {activeDoc ? (
          <>
            {/* Header info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
              <div>
                <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                  <BookOpen size={18} className="text-violet-400" />
                  {activeDoc.title}
                </h1>
                <div className="flex items-center gap-1.5 mt-1">
                  <Calendar size={12} className="text-zinc-500" />
                  <span className="text-[10px] text-zinc-500">
                    Updated {new Date(activeDoc.updated_at || Date.now()).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </span>
                  <span className="text-[10px] bg-zinc-800 text-zinc-400 border border-zinc-700 px-1.5 py-0.5 rounded font-mono uppercase ml-2">
                    {activeDoc.doc_type}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <button
                onClick={handleCopy}
                className="btn-secondary py-2 px-3 text-xs flex items-center gap-1.5 bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-300 font-semibold"
              >
                {copied ? (
                  <>
                    <Check size={13} className="text-emerald-400" /> Copied!
                  </>
                ) : (
                  <>
                    <Copy size={13} /> Copy Markdown
                  </>
                )}
              </button>
            </div>

            {/* Markdown Body */}
            <div className="markdown-body flex-1 max-w-4xl">
              <ReactMarkdown components={renderers}>
                {activeDoc.content}
              </ReactMarkdown>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <Sparkles size={28} className="text-zinc-600 animate-pulse mb-3" />
            <h3 className="text-sm font-bold text-zinc-400">Select a document</h3>
            <p className="text-xs text-zinc-500 mt-1">Choose a markdown guide from the list on the left to read.</p>
          </div>
        )}
      </div>
    </div>
  );
}
