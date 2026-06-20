import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,
  Position,
  NodeProps,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { architectureService } from '../../services/endpoints';
import {
  Network, Search, SlidersHorizontal, Globe, Database,
  Cpu, FileCode, HelpCircle, Activity
} from 'lucide-react';

// Custom custom node component
const ArchitectureNode = ({ data, selected }: NodeProps) => {
  const getBorderColor = () => {
    switch (data.layer) {
      case 'frontend': return 'border-violet-500/80 shadow-violet-500/10';
      case 'backend': return 'border-cyan-500/80 shadow-cyan-500/10';
      case 'database': return 'border-emerald-500/80 shadow-emerald-500/10';
      case 'external': return 'border-amber-500/80 shadow-amber-500/10';
      default: return 'border-zinc-800 shadow-zinc-950/30';
    }
  };

  const getBgColor = () => {
    switch (data.layer) {
      case 'frontend': return 'bg-violet-950/20';
      case 'backend': return 'bg-cyan-950/20';
      case 'database': return 'bg-emerald-950/20';
      case 'external': return 'bg-amber-950/20';
      default: return 'bg-zinc-900/40';
    }
  };

  const getBadgeColor = () => {
    switch (data.type) {
      case 'frontend': return 'bg-violet-500/10 text-violet-400 border-violet-500/20';
      case 'route': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'service': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'model': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'database': return 'bg-teal-500/10 text-teal-400 border-teal-500/20';
      case 'external': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default: return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20';
    }
  };

  const getIcon = () => {
    switch (data.type) {
      case 'frontend': return <Globe size={11} className="text-violet-400" />;
      case 'route': return <Globe size={11} className="text-blue-400" />;
      case 'service': return <Cpu size={11} className="text-cyan-400" />;
      case 'model': return <Database size={11} className="text-emerald-400" />;
      case 'database': return <Database size={11} className="text-teal-400" />;
      default: return <FileCode size={11} className="text-zinc-400" />;
    }
  };

  return (
    <div className={`px-4 py-3 rounded-xl border ${getBgColor()} ${getBorderColor()} shadow-lg transition-all duration-300 ${selected ? 'ring-2 ring-violet-500/50 scale-[1.03] border-violet-400' : ''} text-zinc-100 min-w-[200px]`}>
      <Handle type="target" position={Position.Top} className="w-1.5 h-1.5 bg-zinc-700 border-none" />
      <div className="flex flex-col gap-1.5">
        <div className="flex justify-between items-center gap-2">
          <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md border flex items-center gap-1 ${getBadgeColor()}`}>
            {getIcon()}
            {data.type}
          </span>
          {data.properties?.method && (
            <span className="text-[8px] font-extrabold font-mono text-zinc-400 bg-zinc-800 px-1 py-0.5 rounded">
              {data.properties.method}
            </span>
          )}
        </div>
        <div className="text-xs font-bold text-zinc-200 truncate">{data.label}</div>
        {data.properties?.file_path && (
          <div className="text-[9px] text-zinc-500 truncate font-mono">{data.properties.file_path}</div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-1.5 h-1.5 bg-zinc-700 border-none" />
    </div>
  );
};

const nodeTypes = {
  architectureNode: ArchitectureNode,
};

// Dagre Layout config
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 220, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      targetPosition: isHorizontal ? Position.Left : Position.Top,
      sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
      position: {
        x: nodeWithPosition.x - 110,
        y: nodeWithPosition.y - 40,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

export default function RepoArchitecturePage() {
  const { id } = useParams<{ id: string }>();
  const [direction, setDirection] = useState<'TB' | 'LR'>('TB');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  
  // Layer filters state
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    frontend: true,
    backend: true,
    database: true,
    external: true,
  });

  // Highlighted dependencies tracking
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // Fetch graph details
  const { data: rawGraph, isLoading, error } = useQuery({
    queryKey: ['repoArchitecture', id],
    queryFn: () => architectureService.get(id!),
    enabled: !!id,
  });

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Compute graph layouts on data fetch
  useEffect(() => {
    if (rawGraph) {
      // Filter nodes based on layer toggle
      const filteredNodes = rawGraph.nodes.filter(
        (n: any) => activeLayers[n.layer]
      );

      const filteredNodeIds = new Set(filteredNodes.map((n: any) => n.id));
      const filteredEdges = rawGraph.edges.filter(
        (e: any) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
      );

      // Create React Flow node structures
      const rfNodes = filteredNodes.map((n: any) => ({
        id: n.id,
        type: 'architectureNode',
        data: {
          label: n.label,
          type: n.type,
          layer: n.layer,
          properties: n.properties,
        },
        position: { x: 0, y: 0 }, // Position will be set by dagre layout
      }));

      const rfEdges = filteredEdges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        animated: true,
        type: 'default',
        style: { stroke: '#27272a', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#27272a',
        },
      }));

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        rfNodes,
        rfEdges,
        direction
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
  }, [rawGraph, activeLayers, direction, setNodes, setEdges]);

  // Update styles for searched / highlighted nodes & edges
  const processedElements = useMemo(() => {
    // Collect highlight paths if node is hovered
    const highlightedNodeIds = new Set<string>();
    const highlightedEdgeIds = new Set<string>();

    if (hoveredNodeId) {
      highlightedNodeIds.add(hoveredNodeId);
      edges.forEach((edge) => {
        if (edge.source === hoveredNodeId) {
          highlightedNodeIds.add(edge.target);
          highlightedEdgeIds.add(edge.id);
        }
        if (edge.target === hoveredNodeId) {
          highlightedNodeIds.add(edge.source);
          highlightedEdgeIds.add(edge.id);
        }
      });
    }

    const updatedNodes = nodes.map((node) => {
      const isMatch = searchQuery
        ? node.data.label.toLowerCase().includes(searchQuery.toLowerCase())
        : true;

      const isHighlighted = hoveredNodeId ? highlightedNodeIds.has(node.id) : true;

      return {
        ...node,
        style: {
          ...node.style,
          opacity: isMatch && isHighlighted ? 1 : 0.25,
          boxShadow: isMatch && searchQuery ? '0 0 16px rgba(139, 92, 246, 0.4)' : undefined,
        },
      };
    });

    const updatedEdges = edges.map((edge) => {
      const isPath = hoveredNodeId ? highlightedEdgeIds.has(edge.id) : false;

      return {
        ...edge,
        animated: isPath || edge.animated,
        style: {
          ...edge.style,
          stroke: isPath ? '#8b5cf6' : hoveredNodeId ? '#27272a' : '#52525b',
          strokeWidth: isPath ? 2.5 : 1.5,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isPath ? '#8b5cf6' : hoveredNodeId ? '#27272a' : '#52525b',
        },
      };
    });

    return { nodes: updatedNodes, edges: updatedEdges };
  }, [nodes, edges, searchQuery, hoveredNodeId]);

  const onNodeClick = useCallback((_: any, node: any) => {
    setSelectedNode(node);
  }, []);

  const toggleLayer = (layer: string) => {
    setActiveLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  };

  if (isLoading) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-zinc-500 text-sm font-medium">Generating service visualization map...</p>
        </div>
      </div>
    );
  }

  if (error || !rawGraph) {
    return (
      <div className="flex-1 bg-zinc-950 flex items-center justify-center p-6 text-center">
        <div className="max-w-md glass-card p-8 border-red-500/20 bg-red-500/5">
          <Network size={32} className="text-red-400 mx-auto mb-3" />
          <h2 className="text-base font-bold text-zinc-200">Visualization Failed</h2>
          <p className="text-xs text-zinc-500 mt-2">
            Failed to parse code imports and construct dependencies graph.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-zinc-950 text-zinc-100 flex flex-col h-full relative overflow-hidden">
      {/* Upper Options Bar */}
      <div className="border-b border-zinc-800/60 p-4 flex flex-wrap items-center justify-between gap-4 bg-zinc-900/10 backdrop-blur z-10">
        <div>
          <h1 className="text-sm font-bold flex items-center gap-2">
            <Network size={16} className="text-violet-400 animate-pulse" />
            Repository Architecture Visualizer
          </h1>
          <p className="text-[10px] text-zinc-500">
            Interactive mapping of frontend endpoints, system layers, models, and service dependencies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search bar */}
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-zinc-900/65 border border-zinc-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-violet-500 w-44 transition-all"
            />
          </div>

          {/* Flow Direction Toggle */}
          <div className="flex bg-zinc-900 rounded-lg p-0.5 border border-zinc-800">
            <button
              onClick={() => setDirection('TB')}
              className={`px-2 py-1 text-[10px] font-bold rounded-md transition-all ${direction === 'TB' ? 'bg-zinc-800 text-violet-400' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              Vertical
            </button>
            <button
              onClick={() => setDirection('LR')}
              className={`px-2 py-1 text-[10px] font-bold rounded-md transition-all ${direction === 'LR' ? 'bg-zinc-800 text-violet-400' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              Horizontal
            </button>
          </div>
        </div>
      </div>

      {/* Main visual map workspace */}
      <div className="flex-1 flex relative">
        {/* Left Side Settings Panel */}
        <div className="w-56 border-r border-zinc-800/40 bg-zinc-950/85 backdrop-blur p-4 flex flex-col gap-5 z-10 overflow-y-auto">
          <div>
            <div className="text-[10px] font-extrabold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5 mb-3">
              <SlidersHorizontal size={12} />
              Layer Filtering
            </div>
            <div className="space-y-2">
              {Object.keys(activeLayers).map((layer) => (
                <label key={layer} className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={activeLayers[layer]}
                    onChange={() => toggleLayer(layer)}
                    className="sr-only"
                  />
                  <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-all ${activeLayers[layer] ? 'bg-violet-600 border-violet-500' : 'border-zinc-800 bg-zinc-900 group-hover:border-zinc-700'}`}>
                    {activeLayers[layer] && <div className="w-1.5 h-1.5 bg-zinc-100 rounded-sm" />}
                  </div>
                  <span className="text-xs text-zinc-400 group-hover:text-zinc-300 capitalize">
                    {layer} layer
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-zinc-800/40">
            <div className="text-[10px] font-extrabold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5 mb-3">
              <Activity size={12} />
              Statistics
            </div>
            <div className="space-y-1.5 text-[11px] text-zinc-400">
              <div className="flex justify-between">
                <span>Total Nodes</span>
                <span className="font-bold text-zinc-200">{nodes.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Total Connections</span>
                <span className="font-bold text-zinc-200">{edges.length}</span>
              </div>
            </div>
          </div>

          <div className="mt-auto p-3 rounded-lg bg-violet-950/15 border border-violet-900/20 text-[10px] text-zinc-500 leading-normal flex items-start gap-2">
            <HelpCircle size={14} className="text-violet-400 shrink-0 mt-0.5" />
            <span>Hover on a node to isolate and highlight its direct dependency linkages. Click a node to view properties.</span>
          </div>
        </div>

        {/* React Flow Board */}
        <div className="flex-1 h-full bg-zinc-950/90 relative">
          <ReactFlow
            nodes={processedElements.nodes}
            edges={processedElements.edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            onNodeMouseEnter={(_, node) => setHoveredNodeId(node.id)}
            onNodeMouseLeave={() => setHoveredNodeId(null)}
            fitView
            minZoom={0.2}
            maxZoom={1.5}
          >
            <Background color="#27272a" gap={16} size={1} />
            <Controls className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden shadow-xl" />
            <MiniMap
              nodeColor={(node) => {
                switch (node.data.layer) {
                  case 'frontend': return '#8b5cf6';
                  case 'backend': return '#06b6d4';
                  case 'database': return '#10b981';
                  case 'external': return '#f59e0b';
                  default: return '#27272a';
                }
              }}
              maskColor="rgba(9, 9, 11, 0.75)"
              className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden hidden md:block"
            />
          </ReactFlow>
        </div>

        {/* Right Info Drawer (Dynamic) */}
        {selectedNode && (
          <div className="w-80 border-l border-zinc-800/40 bg-zinc-950/90 backdrop-blur p-5 flex flex-col gap-4 z-10 overflow-y-auto">
            <div className="flex justify-between items-start gap-4">
              <div>
                <span className="text-[9px] font-bold uppercase tracking-wider text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded-md border border-zinc-700">
                  {selectedNode.data.type}
                </span>
                <h3 className="text-sm font-bold text-zinc-100 mt-2 break-all">{selectedNode.data.label}</h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-zinc-500 hover:text-zinc-300 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 pt-4 border-t border-zinc-850">
              {selectedNode.data.properties?.file_path && (
                <div>
                  <div className="text-[10px] text-zinc-500 font-bold uppercase">File Location</div>
                  <div className="text-xs text-zinc-300 font-mono mt-1 break-all bg-zinc-900/40 p-2 border border-zinc-850 rounded-lg">
                    {selectedNode.data.properties.file_path}
                  </div>
                </div>
              )}

              {selectedNode.data.properties?.desc && (
                <div>
                  <div className="text-[10px] text-zinc-500 font-bold uppercase">Description</div>
                  <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                    {selectedNode.data.properties.desc}
                  </p>
                </div>
              )}

              {selectedNode.data.properties?.definition && (
                <div>
                  <div className="text-[10px] text-zinc-500 font-bold uppercase">Definition Summary</div>
                  <pre className="text-[10px] text-zinc-400 font-mono mt-1.5 p-2 bg-zinc-900/60 border border-zinc-850 rounded-lg overflow-x-auto max-h-40 whitespace-pre-wrap">
                    {selectedNode.data.properties.definition}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
