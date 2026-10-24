import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { InteractiveGraph } from '../components/graph/InteractiveGraph';
import { Network, Search, RefreshCw } from 'lucide-react';

export const GraphVisualizerPage: React.FC = () => {
  const [graphData, setGraphData] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchGraph = () => {
    setLoading(true);
    api.get('/graph/topology')
      .then(res => setGraphData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  const filteredNodes = graphData?.nodes?.filter((n: any) => 
    n.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    n.owner.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-5 select-none">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#202A35] pb-3">
        <div>
          <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight flex items-center space-x-2">
            <Network className="w-4 h-4 text-[#3B82F6]" />
            <span>Interactive Account & Transaction Graph Explorer</span>
          </h1>
          <p className="text-[11px] text-[#8995A3] mt-0.5">Multi-hop path traversal, Betweenness Centrality, and suspicious subgraph community detection</p>
        </div>

        {/* Search & Refresh Bar */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#5E6A78] absolute left-2.5 top-2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search Account / Customer..."
              className="bg-[#111820] border border-[#202A35] rounded pl-8 pr-3 py-1 text-xs text-[#E8EDF2] focus:outline-none focus:border-[#3B82F6]"
            />
          </div>

          <button 
            onClick={fetchGraph}
            className="p-1.5 bg-[#111820] border border-[#202A35] text-[#8995A3] hover:text-[#E8EDF2] rounded transition-colors"
            title="Refresh Graph Topology"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Graph Canvas */}
      {graphData ? (
        <InteractiveGraph nodes={filteredNodes} edges={graphData.edges} />
      ) : (
        <div className="h-[520px] bg-[#0B0F14] rounded border border-[#202A35] flex items-center justify-center text-[#5E6A78] font-mono text-xs">
          Querying Neo4j Cypher Graph Engine...
        </div>
      )}
    </div>
  );
};
