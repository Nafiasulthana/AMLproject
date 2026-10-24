import React, { useMemo, useState } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  Node, 
  Edge, 
  MarkerType,
  Handle,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AlertTriangle, ArrowRight, ShieldAlert, CheckCircle, Info, X } from 'lucide-react';

export interface Hop {
  step: number;
  sender: string;
  receiver: string;
  amount: number;
  timestamp: string;
  channel: string;
  mule_indicator: string;
  is_layering_hop: boolean;
}

interface FundFlowDiagramProps {
  sourceAccount: string;
  sinkAccount: string;
  hops: Hop[];
  riskFlags: string[];
}

// Custom Node Component for ReactFlow
const AccountNodeComponent: React.FC<{ data: any }> = ({ data }) => {
  const isSource = data.isSource;
  const isSink = data.isSink;
  
  return (
    <div className={`px-4 py-3 rounded-md border text-left min-w-[180px] bg-[#111820] select-none transition-all shadow-md ${
      isSource ? 'border-[#3B82F6] ring-1 ring-[#3B82F6]/30' :
      isSink ? 'border-[#EF4444] ring-1 ring-[#EF4444]/30' :
      'border-[#202A35] hover:border-[#3B82F6]/50'
    }`}>
      <Handle type="target" position={Position.Left} className="w-2 h-2 !bg-[#8995A3] !border-none" />
      
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-mono font-bold text-[#8995A3]">
          {data.role}
        </span>
        <span className={`w-2 h-2 rounded-full ${
          isSink || data.riskLevel === 'CRITICAL' ? 'bg-[#EF4444]' :
          data.riskLevel === 'WARNING' ? 'bg-[#F59E0B]' : 'bg-[#22C55E]'
        }`} />
      </div>

      <div className="text-xs font-mono font-bold text-[#E8EDF2] flex items-center space-x-1">
        <span>{data.label}</span>
      </div>

      <div className="text-[11px] font-mono text-[#3B82F6] font-semibold mt-1">
        ₹{data.amount?.toLocaleString()}
      </div>

      {data.indicator && (
        <div className="text-[9px] text-[#F59E0B] mt-1.5 flex items-center space-x-1 truncate max-w-[160px]" title={data.indicator}>
          <AlertTriangle className="w-2.5 h-2.5 shrink-0" />
          <span className="truncate">{data.indicator}</span>
        </div>
      )}

      <Handle type="source" position={Position.Right} className="w-2 h-2 !bg-[#3B82F6] !border-none" />
    </div>
  );
};

const nodeTypes = {
  accountNode: AccountNodeComponent,
};

export const FundFlowDiagram: React.FC<FundFlowDiagramProps> = ({ 
  sourceAccount, 
  sinkAccount, 
  hops, 
  riskFlags 
}) => {
  const [selectedEntity, setSelectedEntity] = useState<any>(null);

  // Map Hops to ReactFlow Nodes and Edges
  const { nodes, edges } = useMemo(() => {
    if (!hops || hops.length === 0) {
      return { nodes: [], edges: [] };
    }

    const uniqueAccounts: Array<{ id: string; role: string; isSource: boolean; isSink: boolean; amount: number; indicator?: string; riskLevel: string }> = [];
    
    // 1. Add Source
    uniqueAccounts.push({
      id: sourceAccount,
      role: 'SOURCE ACCOUNT',
      isSource: true,
      isSink: false,
      amount: hops[0]?.amount || 500000,
      riskLevel: 'WARNING'
    });

    // 2. Add intermediate receivers & sink
    hops.forEach((hop, idx) => {
      const isLast = idx === hops.length - 1;
      const targetId = hop.receiver;

      if (!uniqueAccounts.some(a => a.id === targetId)) {
        uniqueAccounts.push({
          id: targetId,
          role: isLast ? 'ULTIMATE SINK' : `PASS-THROUGH MULE #${idx + 1}`,
          isSource: false,
          isSink: isLast,
          amount: hop.amount,
          indicator: hop.mule_indicator,
          riskLevel: isLast ? 'CRITICAL' : 'WARNING'
        });
      }
    });

    // Create ReactFlow nodes with horizontal grid spacing
    const flowNodes: Node[] = uniqueAccounts.map((acc, index) => ({
      id: acc.id,
      type: 'accountNode',
      position: { x: index * 240 + 30, y: 80 },
      data: { 
        label: acc.id,
        role: acc.role,
        isSource: acc.isSource,
        isSink: acc.isSink,
        amount: acc.amount,
        indicator: acc.indicator,
        riskLevel: acc.riskLevel
      }
    }));

    // Create ReactFlow edges with transaction labels
    const flowEdges: Edge[] = hops.map((hop) => ({
      id: `edge-${hop.step}-${hop.sender}-${hop.receiver}`,
      source: hop.sender,
      target: hop.receiver,
      animated: true,
      style: { stroke: '#3B82F6', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#3B82F6' },
      label: `₹${(hop.amount / 100000).toFixed(1)}L · ${hop.channel}`,
      labelStyle: { fill: '#8995A3', fontSize: 10, fontFamily: 'monospace', fontWeight: 600 },
      labelBgStyle: { fill: '#111820', fillOpacity: 0.9, rx: 4, ry: 4 },
      data: hop
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [sourceAccount, sinkAccount, hops]);

  return (
    <div className="space-y-5 select-none">
      {/* ReactFlow Interactive Graph Canvas */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4 relative">
        <div className="flex items-center justify-between mb-3 border-b border-[#202A35] pb-2.5">
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#8995A3]">Graph Topology Path</span>
            <span className="text-xs text-[#3B82F6] font-mono font-semibold">
              {sourceAccount} ──► {sinkAccount}
            </span>
          </div>
          <div className="text-[10px] text-[#5E6A78] font-mono">
            Interactive Drag & Zoom Active
          </div>
        </div>

        <div className="h-[260px] w-full bg-[#0B0F14] rounded border border-[#202A35]">
          <ReactFlow 
            nodes={nodes} 
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            onNodeClick={(_, node) => setSelectedEntity({ type: 'ACCOUNT', data: node.data })}
            onEdgeClick={(_, edge) => setSelectedEntity({ type: 'TRANSACTION', data: edge.data })}
            attributionPosition="bottom-right"
          >
            <Background color="#202A35" gap={20} size={1} />
            <Controls />
          </ReactFlow>
        </div>

        {/* Selected Entity Property Inspector Drawer */}
        {selectedEntity && (
          <div className="absolute top-16 right-6 z-20 bg-[#151D26] border border-[#202A35] rounded-md p-3.5 shadow-xl w-64 text-xs">
            <div className="flex items-center justify-between border-b border-[#202A35] pb-2 mb-2">
              <span className="text-[10px] font-bold text-[#3B82F6] uppercase">
                {selectedEntity.type} Inspector
              </span>
              <button onClick={() => setSelectedEntity(null)} className="text-[#8995A3] hover:text-[#E8EDF2]">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            {selectedEntity.type === 'ACCOUNT' ? (
              <div className="space-y-1.5 font-mono text-[11px]">
                <div className="flex justify-between"><span className="text-[#8995A3]">Account ID:</span><span className="text-[#E8EDF2] font-bold">{selectedEntity.data.label}</span></div>
                <div className="flex justify-between"><span className="text-[#8995A3]">Role:</span><span className="text-[#3B82F6] font-bold">{selectedEntity.data.role}</span></div>
                <div className="flex justify-between"><span className="text-[#8995A3]">Last Volume:</span><span className="text-[#EF4444] font-bold">₹{selectedEntity.data.amount?.toLocaleString()}</span></div>
                {selectedEntity.data.indicator && (
                  <div className="text-[10px] text-[#F59E0B] pt-1 font-sans border-t border-[#202A35] mt-1">{selectedEntity.data.indicator}</div>
                )}
              </div>
            ) : (
              <div className="space-y-1.5 font-mono text-[11px]">
                <div className="flex justify-between"><span className="text-[#8995A3]">Step:</span><span className="text-[#E8EDF2] font-bold">Hop #{selectedEntity.data.step}</span></div>
                <div className="flex justify-between"><span className="text-[#8995A3]">From:</span><span className="text-[#E8EDF2]">{selectedEntity.data.sender}</span></div>
                <div className="flex justify-between"><span className="text-[#8995A3]">To:</span><span className="text-[#E8EDF2]">{selectedEntity.data.receiver}</span></div>
                <div className="flex justify-between"><span className="text-[#8995A3]">Amount:</span><span className="text-[#EF4444] font-bold">₹{selectedEntity.data.amount?.toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-[#8995A3]">Channel:</span><span className="text-[#3B82F6]">{selectedEntity.data.channel}</span></div>
                <div className="flex justify-between"><span className="text-[#8995A3]">Time:</span><span className="text-[#8995A3]">{selectedEntity.data.timestamp}</span></div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
