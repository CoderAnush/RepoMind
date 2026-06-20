import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { diagramService } from '../../services/endpoints';
import mermaid from 'mermaid';
import {
  Network, ZoomIn, ZoomOut, Maximize2, Minimize2,
  Download, RefreshCw, Sparkles, AlertTriangle
} from 'lucide-react';

// Initialize Mermaid configs
try {
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'JetBrains Mono, monospace',
    themeVariables: {
      primaryColor: '#8B5CF6',
      primaryTextColor: '#fff',
      primaryBorderColor: '#8B5CF6',
      lineColor: '#06B6D4',
      secondaryColor: '#06B6D4',
      tertiaryColor: '#111827',
    }
  });
} catch (e) {
  console.error('Mermaid init error:', e);
}

export default function RepoDiagramsPage() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'ARCHITECTURE' | 'CLASS' | 'SEQUENCE' | 'DEPENDENCY'>('ARCHITECTURE');
  const [scale, setScale] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [svgHtml, setSvgHtml] = useState<string>('');
  const [renderError, setRenderError] = useState<string | null>(null);

  // Fetch diagrams list
  const { data: diagrams = [], isLoading, error } = useQuery({
    queryKey: ['diagrams', id],
    queryFn: () => diagramService.list(id!),
    enabled: !!id,
  });

  const activeDiagram = useMemo(() => {
    return diagrams.find(d => d.diagram_type === activeTab) || null;
  }, [diagrams, activeTab]);

  // Render Mermaid code to SVG whenever active diagram changes
  useEffect(() => {
    setRenderError(null);
    setSvgHtml('');
    
    if (!activeDiagram?.code) return;

    const renderId = `mermaid-canvas-${activeDiagram.id}`;
    
    // Clear out element if it exists to avoid duplications
    const runRenderer = async () => {
      try {
        const { svg } = await mermaid.render(renderId, activeDiagram.code);
        setSvgHtml(svg);
      } catch (err: any) {
        console.error('Mermaid render error:', err);
        setRenderError('Mermaid layout compilation failed. Syntax tree mismatch.');
        // Clean up broken elements
        const badgeElem = document.getElementById(renderId);
        if (badgeElem) badgeElem.remove();
      }
    };

    runRenderer();
  }, [activeDiagram]);

  const handleZoomIn = () => setScale(s => Math.min(s + 0.15, 3));
  const handleZoomOut = () => setScale(s => Math.max(s - 0.15, 0.4));
  const handleResetZoom = () => setScale(1);

  const getExportUrl = (format: 'png' | 'svg') => {
    if (!activeDiagram) return '#';
    const apiBase = import.meta.env.VITE_API_URL || 'https://repomind-api-z6x5.onrender.com/api/v1';
    return `${apiBase}/repositories/${id}/diagrams/${activeDiagram.id}/${format}`;
  };

  const tabs: { type: typeof activeTab; label: string }[] = [
    { type: 'ARCHITECTURE', label: 'System Architecture' },
    { type: 'CLASS', label: 'Class Relations' },
    { type: 'SEQUENCE', label: 'Sequence Flow' },
    { type: 'DEPENDENCY', label: 'File Dependencies' },
  ];

  if (isLoading) {
    return (
      <div className="flex-1 bg-zinc-950 flex flex-col p-6 md:p-8 space-y-6">
        <div className="skeleton h-12 w-full" />
        <div className="skeleton h-8 w-1/3" />
        <div className="skeleton h-96 w-full flex-1" />
      </div>
    );
  }

  if (error || diagrams.length === 0) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center p-6 text-center">
        <div className="max-w-md glass-card p-8 border-zinc-850 bg-zinc-900/10">
          <AlertTriangle size={32} className="text-zinc-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-zinc-200">No Diagrams Generated</h2>
          <p className="text-xs text-zinc-500 mt-2">
            No diagrams could be constructed for this workspace. Wait for analysis pipelines to compile.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-zinc-950 p-6 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800/60 pb-5">
        <div>
          <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <Network size={18} className="text-violet-400" />
            Diagram Viewer
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">Explore class linkages, dependency graphs, and call sequences.</p>
        </div>

        {/* Action bar */}
        {activeDiagram && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomIn}
              className="p-2 rounded bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Zoom In"
            >
              <ZoomIn size={14} />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 rounded bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Zoom Out"
            >
              <ZoomOut size={14} />
            </button>
            <button
              onClick={handleResetZoom}
              className="px-2.5 py-2 rounded bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-[10px] text-zinc-400 hover:text-zinc-200 font-bold transition-colors"
            >
              Reset
            </button>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 rounded bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
              title="Fullscreen"
            >
              <Maximize2 size={14} />
            </button>

            <a
              href={getExportUrl('svg')}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary py-2 px-3 text-xs flex items-center gap-1 bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-300 font-semibold"
            >
              <Download size={12} /> SVG
            </a>
            <a
              href={getExportUrl('png')}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary py-2 px-3 text-xs flex items-center gap-1 bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-300 font-semibold"
            >
              <Download size={12} /> PNG
            </a>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-zinc-800/60 pb-px">
        {tabs.map((tab) => (
          <button
            key={tab.type}
            onClick={() => {
              setActiveTab(tab.type);
              setScale(1);
            }}
            className={
              activeTab === tab.type
                ? 'tab-item-active text-xs font-semibold'
                : 'tab-item-inactive text-xs font-semibold'
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Canvas */}
      <div className="flex-1 glass-card border border-zinc-850 rounded-xl relative overflow-hidden bg-zinc-950/40 flex items-center justify-center p-6 min-h-[300px]">
        {/* Grid pattern overlay for canvas background */}
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.1] pointer-events-none" />

        {renderError ? (
          <div className="text-center max-w-sm">
            <AlertTriangle size={24} className="text-amber-400 mx-auto mb-2" />
            <h4 className="text-xs font-bold text-zinc-200">Renderer Warning</h4>
            <p className="text-[10px] text-zinc-500 mt-1">{renderError}</p>
          </div>
        ) : svgHtml ? (
          <div
            className="mermaid-wrapper flex items-center justify-center transition-transform duration-200 select-none cursor-grab active:cursor-grabbing"
            style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}
            dangerouslySetInnerHTML={{ __html: svgHtml }}
          />
        ) : (
          <div className="flex flex-col items-center gap-2">
            <RefreshCw size={20} className="text-violet-400 animate-spin" />
            <span className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider">Parsing Mermaid syntax...</span>
          </div>
        )}
      </div>

      {/* Fullscreen Overlay */}
      {isFullscreen && activeDiagram && (
        <div className="fixed inset-0 z-50 bg-zinc-950/95 flex flex-col p-6">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4 mb-4">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-violet-400" />
              <span className="text-sm font-bold text-zinc-200">{activeDiagram.diagram_type} Diagram</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleZoomIn}
                className="p-2 rounded bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-400"
              >
                <ZoomIn size={14} />
              </button>
              <button
                onClick={handleZoomOut}
                className="p-2 rounded bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-400"
              >
                <ZoomOut size={14} />
              </button>
              <button
                onClick={() => setIsFullscreen(false)}
                className="btn-secondary py-2 px-3 text-xs flex items-center gap-1"
              >
                <Minimize2 size={12} /> Close Fullscreen
              </button>
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center overflow-auto p-12">
            {svgHtml && (
              <div
                className="mermaid-wrapper flex items-center justify-center transition-transform duration-200"
                style={{ transform: `scale(${scale})` }}
                dangerouslySetInnerHTML={{ __html: svgHtml }}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
