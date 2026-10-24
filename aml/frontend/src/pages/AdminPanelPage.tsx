import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Sliders, Activity, Database, Brain, Users, RefreshCw, CheckCircle2 } from 'lucide-react';

export const AdminPanelPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [rules, setRules] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [retraining, setRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState('');

  const fetchAdminData = () => {
    api.get('/admin/health').then(res => setHealth(res.data)).catch(() => {});
    api.get('/admin/rules').then(res => setRules(res.data)).catch(() => {});
    api.get('/admin/users').then(res => setUsers(res.data)).catch(() => {});
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainMsg('');
    try {
      const res = await api.post('/admin/retrain-ml');
      setRetrainMsg(res.data.message);
      fetchAdminData();
    } catch (err: any) {
      setRetrainMsg('Retraining failed.');
    } finally {
      setRetraining(false);
    }
  };

  const handleToggleRule = async (ruleCode: string, currentThresh: number, currentWeight: number, currentEnabled: boolean) => {
    await api.put(`/admin/rules/${ruleCode}`, null, {
      params: {
        threshold: currentThresh,
        weight: currentWeight,
        enabled: !currentEnabled
      }
    });
    fetchAdminData();
  };

  return (
    <div className="space-y-5 select-none">
      <div className="border-b border-[#202A35] pb-3">
        <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-[#3B82F6]" />
          <span>System Administration & Compliance Rules Matrix</span>
        </h1>
        <p className="text-[11px] text-[#8995A3] mt-0.5">Configure AML detection thresholds, risk weights, retrain XGBoost ML model, and monitor engine status</p>
      </div>

      {/* System Health Indicators */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {Object.entries(health.services || {}).map(([service, status]: [string, any], idx) => (
            <div key={idx} className="bg-[#111820] p-3 rounded border border-[#202A35]">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider">{service.replace(/_/g, ' ')}</span>
                <Activity className="w-3.5 h-3.5 text-[#22C55E]" />
              </div>
              <div className="text-xs font-bold font-mono text-[#22C55E]">{status}</div>
            </div>
          ))}
        </div>
      )}

      {/* ML Model Retraining Trigger Box */}
      <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35] flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-[#151D26] border border-[#202A35] flex items-center justify-center text-[#3B82F6]">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-[#E8EDF2]">XGBoost ML Risk Engine Retraining</h3>
            <p className="text-[11px] text-[#8995A3]">Explicitly triggers decision boundary retraining on Phase 1 dataset with seed 42</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {retrainMsg && <span className="text-xs text-[#22C55E] font-mono">{retrainMsg}</span>}
          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="px-3 py-1.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white text-xs font-semibold rounded flex items-center space-x-1.5 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${retraining ? 'animate-spin' : ''}`} />
            <span>{retraining ? 'Retraining XGBoost...' : 'Trigger Model Retraining'}</span>
          </button>
        </div>
      </div>

      {/* Configurable AML Rules Table */}
      <div className="bg-[#111820] p-4 rounded-lg border border-[#202A35] space-y-3">
        <h2 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider border-b border-[#202A35] pb-2">AML Detection Rules & Risk Weight Matrix</h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-[#202A35] text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider font-sans">
                <th className="py-2 px-3">Rule Code</th>
                <th className="py-2 px-3">Name</th>
                <th className="py-2 px-3">Typology</th>
                <th className="py-2 px-3">Threshold</th>
                <th className="py-2 px-3">Risk Weight</th>
                <th className="py-2 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202A35]/60 text-[#E8EDF2]">
              {rules.map((rule) => (
                <tr key={rule.rule_code} className="hover:bg-[#151D26] transition-colors">
                  <td className="py-2 px-3 text-[#3B82F6] font-bold">{rule.rule_code}</td>
                  <td className="py-2 px-3 text-[#E8EDF2] font-sans font-semibold">{rule.name}</td>
                  <td className="py-2 px-3 font-sans">
                    <span className="bg-[#151D26] text-[#B0BAC5] px-2 py-0.5 rounded text-[10px] border border-[#202A35]">
                      {rule.typology}
                    </span>
                  </td>
                  <td className="py-2 px-3">₹{rule.threshold_value?.toLocaleString()}</td>
                  <td className="py-2 px-3 font-bold text-[#F59E0B]">+{rule.risk_weight}%</td>
                  <td className="py-2 px-3 text-right font-sans">
                    <button
                      onClick={() => handleToggleRule(rule.rule_code, rule.threshold_value, rule.risk_weight, rule.is_enabled)}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rule.is_enabled ? 'bg-[#151D26] text-[#22C55E] border border-[#22C55E]/40' : 'bg-[#151D26] text-[#5E6A78] border border-[#202A35]'
                      }`}
                    >
                      {rule.is_enabled ? 'ENABLED' : 'DISABLED'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
