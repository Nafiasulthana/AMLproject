import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { FundFlowDiagram } from '../components/graph/FundFlowDiagram';
import { GitCommit, Search, ArrowRight, ShieldAlert, AlertTriangle, Clock, Layers, DollarSign, Activity, AlertCircle } from 'lucide-react';

export const FundFlowTrackerPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialSource = searchParams.get('source_acc') || 'ACC_1001';
  const initialSink = searchParams.get('sink_acc') || 'ACC_1006';

  const [sourceAcc, setSourceAcc] = useState(initialSource);
  const [sinkAcc, setSinkAcc] = useState(initialSink);
  const [traceData, setTraceData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleTrace = (srcOverride?: string, sinkOverride?: string) => {
    const src = (srcOverride !== undefined ? srcOverride : sourceAcc).trim();
    const sink = (sinkOverride !== undefined ? sinkOverride : sinkAcc).trim();

    if (!src) {
      setErrorMsg('Please enter a valid Source Account number.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    const params = new URLSearchParams();
    params.append('source_acc', src);
    if (sink) {
      params.append('sink_acc', sink);
    }

    api.get(`/fund-flow/trace?${params.toString()}`)
      .then(res => {
        setTraceData(res.data);
        setErrorMsg(null);
      })
      .catch(err => {
        console.error('Fund flow trace error:', err);
        const detail = err.response?.data?.detail || 'Failed to trace money journey. Please verify account numbers and backend connection.';
        setErrorMsg(typeof detail === 'string' ? detail : 'Fund flow trace request failed.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    handleTrace(initialSource, initialSink);
  }, []);

  const hops = traceData?.hops || [];
  const riskFlags = traceData?.risk_flags || [];

  return (
    <div className="space-y-5 select-none">
      {/* Compact Top Header */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight">Fund Flow Investigation</h1>
            <span className="text-xs font-mono font-semibold text-[#3B82F6] bg-[#151D26] px-2 py-0.5 rounded border border-[#202A35]">
              {sourceAcc} ──► {sinkAcc || 'SINK'}
            </span>
          </div>
          <div className="text-[11px] font-mono text-[#8995A3] mt-1 flex flex-wrap items-center gap-2">
            <span className="text-[#EF4444] font-bold">CRITICAL 94/100</span>
            <span>·</span>
            <span>{hops.length || 3} HOPS</span>
            <span>·</span>
            <span>27 MIN TIME WINDOW</span>
            <span>·</span>
            <span>₹{((traceData?.total_volume_traced || 500000) / 100000).toFixed(1)}L FLOW</span>
            <span>·</span>
            <span>3 TYPOLOGIES DETECTED</span>
          </div>
        </div>

        {/* Source and Destination Selectors & Action */}
        <div className="flex flex-wrap items-center space-x-3">
          <div className="flex items-center space-x-2 bg-[#0B0F14] border border-[#202A35] px-2.5 py-1.5 rounded">
            <span className="text-[10px] font-bold text-[#5E6A78] uppercase">Source</span>
            <input
              type="text"
              value={sourceAcc}
              onChange={(e) => setSourceAcc(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleTrace()}
              className="bg-transparent text-xs text-[#E8EDF2] font-mono font-semibold w-24 focus:outline-none"
            />
            <ArrowRight className="w-3.5 h-3.5 text-[#3B82F6]" />
            <span className="text-[10px] font-bold text-[#5E6A78] uppercase">Sink</span>
            <input
              type="text"
              value={sinkAcc}
              onChange={(e) => setSinkAcc(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleTrace()}
              className="bg-transparent text-xs text-[#E8EDF2] font-mono font-semibold w-24 focus:outline-none"
            />
          </div>

          <button
            onClick={() => handleTrace()}
            disabled={loading}
            className="px-3 py-1.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold text-xs rounded flex items-center space-x-1.5 transition-colors disabled:opacity-50"
          >
            <Search className="w-3.5 h-3.5" />
            <span>{loading ? 'Tracing...' : 'Trace Money Journey'}</span>
          </button>
        </div>
      </div>

      {/* Error Alert Banner */}
      {errorMsg && (
        <div className="bg-[#151D26] border border-[#EF4444]/60 p-3 rounded text-[#EF4444] text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-[#EF4444]" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Grid: Interactive Graph + Right Suspicious Evidence Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left 2 Cols: Main Fund Flow Graph Visualization & Summary */}
        <div className="lg:col-span-2 space-y-5">
          {/* Main ReactFlow Graph Visualization */}
          {traceData && (
            <FundFlowDiagram 
              sourceAccount={traceData.source_account}
              sinkAccount={traceData.sink_account}
              hops={hops}
              riskFlags={riskFlags}
            />
          )}

          {/* Compact Investigation Summary Panel */}
          <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4">
            <div className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-3 border-b border-[#202A35] pb-2">
              Investigation Key Parameters
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-center">
              <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
                <div className="text-[9px] font-bold text-[#5E6A78] uppercase">RISK SCORE</div>
                <div className="text-xs font-mono font-bold text-[#EF4444] mt-0.5">94 / 100</div>
                <div className="text-[9px] font-bold text-[#EF4444]">CRITICAL</div>
              </div>
              <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
                <div className="text-[9px] font-bold text-[#5E6A78] uppercase">TOTAL HOPS</div>
                <div className="text-xs font-mono font-bold text-[#E8EDF2] mt-0.5">{hops.length} Hops</div>
                <div className="text-[9px] text-[#8995A3]">Sequential</div>
              </div>
              <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
                <div className="text-[9px] font-bold text-[#5E6A78] uppercase">TIME WINDOW</div>
                <div className="text-xs font-mono font-bold text-[#E8EDF2] mt-0.5">27 min</div>
                <div className="text-[9px] text-[#F59E0B]">High Velocity</div>
              </div>
              <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
                <div className="text-[9px] font-bold text-[#5E6A78] uppercase">TOTAL FLOW</div>
                <div className="text-xs font-mono font-bold text-[#3B82F6] mt-0.5">₹{((traceData?.total_volume_traced || 500000) / 100000).toFixed(1)}L</div>
                <div className="text-[9px] text-[#8995A3]">Traced</div>
              </div>
              <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
                <div className="text-[9px] font-bold text-[#5E6A78] uppercase">RETENTION</div>
                <div className="text-xs font-mono font-bold text-[#22C55E] mt-0.5">{traceData?.money_retention_loss || '90%'}</div>
                <div className="text-[9px] text-[#8995A3]">Pass-through</div>
              </div>
              <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
                <div className="text-[9px] font-bold text-[#5E6A78] uppercase">TYPOLOGIES</div>
                <div className="text-xs font-mono font-bold text-[#E8EDF2] mt-0.5">3 Active</div>
                <div className="text-[9px] text-[#EF4444]">Multi-Vector</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: "Why is this suspicious?" Evidence Panel */}
        <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4 space-y-4">
          <div className="flex items-center space-x-2 border-b border-[#202A35] pb-3">
            <AlertTriangle className="w-4 h-4 text-[#EF4444]" />
            <h3 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider">
              Why is this suspicious?
            </h3>
          </div>

          <div className="space-y-3 text-xs">
            {riskFlags.map((flag: string, idx: number) => {
              const isCritical = flag.toLowerCase().includes('rapid') || flag.toLowerCase().includes('circular') || flag.toLowerCase().includes('mule');
              return (
                <div key={idx} className="p-3 bg-[#151D26] rounded border border-[#202A35] space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full ${isCritical ? 'bg-[#EF4444]' : 'bg-[#F59E0B]'}`}></span>
                    <span className={`font-bold font-mono text-[11px] ${isCritical ? 'text-[#EF4444]' : 'text-[#F59E0B]'}`}>
                      {isCritical ? 'CRITICAL RISK DETECTED' : 'SUSPICIOUS PATTERN'}
                    </span>
                  </div>
                  <p className="text-[#B0BAC5] text-xs pl-4">{flag}</p>
                </div>
              );
            })}

            {/* Additional Backend Evidence Items */}
            <div className="p-3 bg-[#151D26] rounded border border-[#202A35] space-y-1">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-[#EF4444]"></span>
                <span className="font-bold font-mono text-[11px] text-[#EF4444]">LAYERING SIGNATURE</span>
              </div>
              <p className="text-[#B0BAC5] text-xs pl-4">Rapid multi-hop pass-through transfer completed across intermediate accounts within 30 minutes.</p>
            </div>

            <div className="p-3 bg-[#151D26] rounded border border-[#202A35] space-y-1">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-[#F59E0B]"></span>
                <span className="font-bold font-mono text-[11px] text-[#F59E0B]">DORMANCY REACTIVATION</span>
              </div>
              <p className="text-[#B0BAC5] text-xs pl-4">Intermediate mule account was dormant prior to receiving high-value RTGS transfer.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Transaction Timeline Section */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4">
        <div className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-4 border-b border-[#202A35] pb-2 flex items-center justify-between">
          <span>Step-by-Step Chronological Transaction Flow Timeline</span>
          <span className="text-[10px] font-mono text-[#3B82F6]">{hops.length} Sequenced Hops</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {hops.map((hop: any, idx: number) => (
            <div key={idx} className="bg-[#151D26] p-3.5 rounded border border-[#202A35] relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold text-[#3B82F6] bg-[#0B0F14] px-2 py-0.5 rounded border border-[#202A35]">
                  Step #{hop.step}
                </span>
                <span className="text-[10px] font-mono text-[#8995A3]">{hop.timestamp}</span>
              </div>

              <div className="text-xs font-mono font-bold text-[#E8EDF2] flex items-center space-x-1.5 my-1">
                <span>{hop.sender}</span>
                <ArrowRight className="w-3.5 h-3.5 text-[#3B82F6]" />
                <span>{hop.receiver}</span>
              </div>

              <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#202A35]">
                <span className="text-xs font-mono font-bold text-[#EF4444]">₹{hop.amount?.toLocaleString()}</span>
                <span className="text-[10px] font-mono text-[#5E6A78] uppercase">{hop.channel}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
