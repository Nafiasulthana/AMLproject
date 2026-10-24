import React, { useMemo } from 'react';
import ReactFlow, { 
  Controls, 
  Background, 
  Node, 
  Edge, 
  MarkerType 
} from 'reactflow';
import { GraphNode, GraphEdge } from '../../types';

interface InteractiveGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
}

export const InteractiveGraph: React.FC<InteractiveGraphProps> = ({ nodes: rawNodes, edges: rawEdges, onNodeClick }) => {
  const initialNodes: Node[] = useMemo(() => {
    const positions = [
      { x: 80, y: 140 },
      { x: 420, y: 60 },
      { x: 420, y: 240 },
      { x: 760, y: 140 },
      { x: 260, y: 350 },
      { x: 600, y: 350 },
      { x: 920, y: 350 }
    ];

    return rawNodes.map((n, idx) => {
      const isSuspicious = n.is_suspicious;
      const pos = positions[idx % positions.length];
      return {
        id: n.id,
        position: pos,
        data: { 
          label: (
            <div className={`p-2.5 rounded border text-left min-w-[150px] bg-[#111820] select-none ${
              isSuspicious 
                ? 'border-[#EF4444] ring-1 ring-[#EF4444]/30' 
                : 'border-[#202A35] hover:border-[#3B82F6]/50'
            }`}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-[#E8EDF2] font-mono">{n.id}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold font-mono ${
                  isSuspicious ? 'bg-[#151D26] text-[#EF4444] border border-[#EF4444]/40' : 'bg-[#151D26] text-[#3B82F6] border border-[#3B82F6]/40'
                }`}>
                  {n.risk_category}
                </span>
              </div>
              <div className="text-[11px] text-[#B0BAC5] font-medium truncate">{n.owner}</div>
              <div className="text-[10px] text-[#5E6A78] font-mono mt-1">₹{n.balance.toLocaleString()} • {n.type}</div>
            </div>
          ) 
        },
      };
    });
  }, [rawNodes]);

  const initialEdges: Edge[] = useMemo(() => {
    return rawEdges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: true,
      style: { stroke: '#3B82F6', strokeWidth: 1.5 },
      labelStyle: { fill: '#8995A3', fontSize: 10, fontFamily: 'monospace' },
      labelBgStyle: { fill: '#111820', fillOpacity: 0.9 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#3B82F6',
      },
    }));
  }, [rawEdges]);

  return (
    <div className="w-full h-[520px] bg-[#0B0F14] rounded border border-[#202A35] relative overflow-hidden select-none">
      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background color="#202A35" gap={20} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  );
};
