import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { InteractiveGraph } from '../components/graph/InteractiveGraph';
import { Brain, User, CreditCard, ShieldAlert, CheckCircle, ArrowRight, FolderPlus, GitCommit } from 'lucide-react';

export const InvestigationWorkspacePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const alertId = searchParams.get('alert') || 'ALT_INIT_1';
  const navigate = useNavigate();

  const [alertData, setAlertData] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get(`/alerts/${alertId}`)
      .then(res => setAlertData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));

    api.get('/graph/topology')
      .then(res => setGraphData(res.data))
      .catch(() => {});
  }, [alertId]);

  if (loading && !alertData) {
    return <div className="p-8 text-center text-[#8995A3] text-xs font-mono">Loading AML Investigation Workstation Context...</div>;
  }

  const alert = alertData?.alert;
  const customer = alertData?.customer;
  const tx = alertData?.transaction;
  const shap = alertData?.shap_explanation;

  return (
    <div className="space-y-5 select-none">
      <div className="flex items-center justify-between border-b border-[#202A35] pb-3">
        <div>
          <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-[#EF4444]" />
            <span>AML Investigation Workstation</span>
          </h1>
          <p className="text-[11px] text-[#8995A3] mt-0.5">Triaging workstation for Alert <span className="font-mono text-[#3B82F6] font-semibold">{alertId}</span></p>
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={() => navigate('/cases')}
            className="px-3 py-1.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold text-xs rounded flex items-center space-x-1.5 transition-colors"
          >
            <FolderPlus className="w-3.5 h-3.5" />
            <span>Open Investigation Case</span>
          </button>
        </div>
      </div>

      {/* Grid Layout: Customer & Account Info vs Risk Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Customer KYC Card */}
        <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35]">
          <div className="flex items-center space-x-3 mb-3 border-b border-[#202A35] pb-3">
            <div className="w-8 h-8 rounded bg-[#151D26] border border-[#202A35] flex items-center justify-center text-[#3B82F6]">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#E8EDF2]">{customer?.full_name || 'Acme Global Exports'}</h3>
              <div className="text-[10px] text-[#8995A3] font-mono">ID: {customer?.customer_id || 'CUST_101'} • {customer?.occupation}</div>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-[#8995A3]">National ID:</span>
              <span className="font-mono font-semibold text-[#E8EDF2]">{customer?.national_id || 'IND100982'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8995A3]">KYC Status:</span>
              <span className="px-1.5 py-0.5 bg-[#151D26] text-[#22C55E] border border-[#22C55E]/40 rounded text-[10px] font-bold">
                {customer?.kyc_status || 'VERIFIED'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8995A3]">Monthly Income:</span>
              <span className="font-mono font-bold text-[#E8EDF2]">₹{(customer?.monthly_income || 2500000).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8995A3]">Risk Category:</span>
              <span className="px-1.5 py-0.5 bg-[#151D26] text-[#EF4444] border border-[#EF4444]/40 rounded text-[10px] font-bold">
                {customer?.risk_category || 'HIGH'}
              </span>
            </div>
          </div>
        </div>

        {/* Flagged Transaction Card */}
        <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35]">
          <div className="flex items-center space-x-3 mb-3 border-b border-[#202A35] pb-3">
            <div className="w-8 h-8 rounded bg-[#151D26] border border-[#202A35] flex items-center justify-center text-[#F59E0B]">
              <CreditCard className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#E8EDF2]">Flagged Transaction Details</h3>
              <div className="text-[10px] text-[#8995A3] font-mono">Tx ID: {tx?.tx_id || 'TX_99218'}</div>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-[#8995A3]">Sender Account:</span>
              <span className="font-mono font-bold text-[#E8EDF2]">{tx?.sender_account || 'ACC_1001'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8995A3]">Receiver Account:</span>
              <span className="font-mono font-bold text-[#E8EDF2]">{tx?.receiver_account || 'ACC_1003'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8995A3]">Amount:</span>
              <span className="font-mono font-bold text-[#EF4444]">₹{(tx?.amount || 500000).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8995A3]">Channel / Location:</span>
              <span className="font-sans text-[#B0BAC5]">{tx?.channel || 'RTGS'} ({tx?.location || 'Mumbai'})</span>
            </div>
            <div className="pt-2 border-t border-[#202A35]">
              <button
                onClick={() => navigate(`/fund-flow?source_acc=${tx?.sender_account || 'ACC_1001'}&sink_acc=${tx?.receiver_account || 'ACC_1003'}`)}
                className="w-full py-1.5 px-3 bg-[#151D26] hover:bg-[#202A35] text-[#3B82F6] border border-[#202A35] rounded text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors"
              >
                <GitCommit className="w-3.5 h-3.5" />
                <span>Trace Money Journey</span>
                <ArrowRight className="w-3.5 h-3.5 ml-auto" />
              </button>
            </div>
          </div>
        </div>

        {/* Multi-Vector Risk Score Breakdown */}
        <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35]">
          <div className="flex items-center justify-between mb-3 border-b border-[#202A35] pb-3">
            <h3 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider">Hybrid Meta-Risk Score</h3>
            <span className="text-xs font-bold text-[#EF4444] font-mono">{alert?.meta_risk_score || 88.5}%</span>
          </div>

          <div className="space-y-2.5">
            {[
              { label: 'Rule Engine Risk', score: alert?.rule_risk || 35.0, color: 'bg-[#F59E0B]' },
              { label: 'Behaviour Z-Score Risk', score: alert?.behaviour_risk || 28.0, color: 'bg-[#3B82F6]' },
              { label: 'Graph Topology Risk', score: alert?.graph_risk || 32.0, color: 'bg-[#3B82F6]' },
              { label: 'XGBoost ML Probability', score: alert?.ml_risk || 92.0, color: 'bg-[#EF4444]' }
            ].map((r, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-[10px]">
                  <span className="text-[#8995A3]">{r.label}</span>
                  <span className="font-mono font-bold text-[#E8EDF2]">{r.score}%</span>
                </div>
                <div className="w-full h-1 bg-[#0B0F14] rounded-full overflow-hidden">
                  <div className={`h-full ${r.color}`} style={{ width: `${r.score}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SHAP Explanation Breakdown Card */}
      {shap && (
        <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35]">
          <h3 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider mb-3 flex items-center space-x-2 border-b border-[#202A35] pb-2">
            <Brain className="w-3.5 h-3.5 text-[#3B82F6]" />
            <span>SHAP Explainable AI Feature Attribution Waterfall</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {shap.shap_values?.map((item: any, idx: number) => (
              <div key={idx} className="p-3 bg-[#151D26] rounded border border-[#202A35]">
                <div className="text-xs font-semibold text-[#E8EDF2] mb-1">{item.label}</div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-[#5E6A78] font-mono">{item.feature}</span>
                  <span className={`text-xs font-bold font-mono ${item.contribution > 0 ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
                    {item.contribution > 0 ? `+${item.contribution}%` : `${item.contribution}%`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interactive Account Graph Visualization */}
      <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35]">
        <h3 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider mb-3 border-b border-[#202A35] pb-2">
          Account Network Graph Topology (Neo4j Cypher Live Mapping)
        </h3>
        {graphData && <InteractiveGraph nodes={graphData.nodes} edges={graphData.edges} />}
      </div>
    </div>
  );
};
