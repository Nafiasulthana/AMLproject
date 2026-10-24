import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Cpu, Play, Pause, Square, Gauge, Zap, ShieldAlert, CheckCircle, Activity } from 'lucide-react';

export const SimulatorPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [speed, setSpeed] = useState<number>(1);
  const [typology, setTypology] = useState<string>('MIXED');

  const fetchStatus = () => {
    api.get('/simulation/status')
      .then(res => {
        setStatus(res.data);
        setSpeed(res.data.speed_multiplier);
        setTypology(res.data.selected_typology);
      });
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    await api.post('/simulation/start');
    fetchStatus();
  };

  const handlePause = async () => {
    await api.post('/simulation/pause');
    fetchStatus();
  };

  const handleResume = async () => {
    await api.post('/simulation/resume');
    fetchStatus();
  };

  const handleStop = async () => {
    await api.post('/simulation/stop');
    fetchStatus();
  };

  const handleApplyConfig = async (newSpeed: number, newTypology: string) => {
    setSpeed(newSpeed);
    setTypology(newTypology);
    await api.post('/simulation/configure', {
      is_running: true,
      speed_multiplier: newSpeed,
      selected_typology: newTypology
    });
    fetchStatus();
  };

  const recentTxs = status?.recent_transactions || [];
  const alertCount = recentTxs.filter((t: any) => t.alert_generated).length;
  const criticalCount = recentTxs.filter((t: any) => t.priority === 'CRITICAL').length;
  const lastTxTime = recentTxs[0]?.timestamp || 'None';

  return (
    <div className="space-y-5 select-none">
      <div className="flex items-center justify-between border-b border-[#202A35] pb-3">
        <div>
          <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-[#3B82F6]" />
            <span>Transaction Simulation Operations Console</span>
          </h1>
          <p className="text-[11px] text-[#8995A3] mt-0.5">Operational controls for streaming synthetic banking transactions into the detection pipeline for scoring</p>
        </div>
      </div>

      {/* Operational Control Console */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#202A35] pb-3">
          <div className="flex items-center space-x-3">
            <span className={`w-2.5 h-2.5 rounded-full ${status?.is_running && !status?.is_paused ? 'bg-[#22C55E]' : 'bg-[#5E6A78]'}`}></span>
            <div>
              <div className="text-xs font-bold text-[#E8EDF2] font-mono">
                SIMULATOR STATUS: {status?.is_running ? (status?.is_paused ? 'PAUSED' : 'ACTIVE') : 'IDLE'}
              </div>
              <div className="text-[10px] text-[#8995A3] font-mono">
                Scoring Model: Fixed XGBoost In-Memory Engine (No Retraining)
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {!status?.is_running ? (
              <button onClick={handleStart} className="px-3 py-1.5 bg-[#22C55E] hover:bg-[#16a34a] text-white font-semibold text-xs rounded flex items-center space-x-1.5 transition-colors">
                <Play className="w-3.5 h-3.5" />
                <span>Start Simulation</span>
              </button>
            ) : status?.is_paused ? (
              <button onClick={handleResume} className="px-3 py-1.5 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold text-xs rounded flex items-center space-x-1.5 transition-colors">
                <Play className="w-3.5 h-3.5" />
                <span>Resume</span>
              </button>
            ) : (
              <button onClick={handlePause} className="px-3 py-1.5 bg-[#F59E0B] hover:bg-[#d97706] text-white font-semibold text-xs rounded flex items-center space-x-1.5 transition-colors">
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            )}

            {status?.is_running && (
              <button onClick={handleStop} className="px-3 py-1.5 bg-[#151D26] text-[#EF4444] border border-[#EF4444]/40 hover:bg-[#EF4444]/10 text-xs font-semibold rounded flex items-center space-x-1.5 transition-colors">
                <Square className="w-3.5 h-3.5" />
                <span>Stop</span>
              </button>
            )}
          </div>
        </div>

        {/* Telemetry Counter Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
            <div className="text-[9px] font-bold text-[#5E6A78] uppercase">RECENT TELEMETRY STREAM</div>
            <div className="text-sm font-mono font-bold text-[#E8EDF2] mt-0.5">{recentTxs.length} Txs</div>
          </div>
          <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
            <div className="text-[9px] font-bold text-[#5E6A78] uppercase">ALERTS GENERATED</div>
            <div className="text-sm font-mono font-bold text-[#F59E0B] mt-0.5">{alertCount} Alerts</div>
          </div>
          <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
            <div className="text-[9px] font-bold text-[#5E6A78] uppercase">CRITICAL ALERTS</div>
            <div className="text-sm font-mono font-bold text-[#EF4444] mt-0.5">{criticalCount} Critical</div>
          </div>
          <div className="bg-[#151D26] p-2.5 rounded border border-[#202A35]">
            <div className="text-[9px] font-bold text-[#5E6A78] uppercase">LAST TRANSACTION</div>
            <div className="text-sm font-mono font-bold text-[#3B82F6] mt-0.5">{lastTxTime}</div>
          </div>
        </div>

        {/* Speed Multiplier & Typology Injection Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-[#202A35]">
          <div>
            <label className="block text-[11px] font-bold text-[#8995A3] uppercase tracking-wider mb-1.5 flex items-center space-x-1.5">
              <Gauge className="w-3.5 h-3.5 text-[#3B82F6]" />
              <span>Speed Multiplier ({speed}x)</span>
            </label>
            <div className="flex items-center space-x-2">
              {[1, 5, 10, 25, 50].map((sp) => (
                <button
                  key={sp}
                  onClick={() => handleApplyConfig(sp, typology)}
                  className={`px-3 py-1 rounded text-xs font-mono font-bold transition-all ${
                    speed === sp ? 'bg-[#3B82F6] text-white' : 'bg-[#151D26] text-[#8995A3] border border-[#202A35] hover:text-[#E8EDF2]'
                  }`}
                >
                  {sp}x
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-[#8995A3] uppercase tracking-wider mb-1.5 flex items-center space-x-1.5">
              <Zap className="w-3.5 h-3.5 text-[#F59E0B]" />
              <span>Target Typology Injection</span>
            </label>
            <select
              value={typology}
              onChange={(e) => handleApplyConfig(speed, e.target.value)}
              className="w-full bg-[#151D26] border border-[#202A35] rounded px-3 py-1 text-xs text-[#E8EDF2] font-semibold focus:outline-none focus:border-[#3B82F6]"
            >
              <option value="MIXED">MIXED (Normal + Random Typologies)</option>
              <option value="STRUCTURING">STRUCTURING (CTR Avoidance &lt; $10k)</option>
              <option value="LAYERING">LAYERING (High-Velocity Multi-Hop)</option>
              <option value="ROUND_TRIP">ROUND TRIPPING (Circular Pass-Through Cycle)</option>
              <option value="DORMANT">DORMANT ACCOUNT REACTIVATION</option>
              <option value="SMURFING">SMURFING (Multi-Sender Aggregation)</option>
              <option value="PROFILE_MISMATCH">PROFILE MISMATCH (Income Anomaly)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Live Generated Transactions Telemetry Feed */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4">
        <div className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-3 border-b border-[#202A35] pb-2 flex items-center justify-between">
          <span>Live Generated Telemetry Stream (Entering AML Scoring Engine)</span>
          <span className="text-[10px] text-[#22C55E] font-mono">Real-Time Scoring Active</span>
        </div>

        <div className="overflow-x-auto max-h-[380px]">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead className="bg-[#0B0F14] text-[#5E6A78] uppercase tracking-wider sticky top-0 border-b border-[#202A35] font-sans text-[10px]">
              <tr>
                <th className="py-2 px-3">Time</th>
                <th className="py-2 px-3">Sender</th>
                <th className="py-2 px-3">Receiver</th>
                <th className="py-2 px-3">Amount</th>
                <th className="py-2 px-3">Channel</th>
                <th className="py-2 px-3">Typology</th>
                <th className="py-2 px-3">Meta Risk</th>
                <th className="py-2 px-3">Alert Trigger</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202A35]/60 text-[#E8EDF2]">
              {recentTxs.map((tx: any, idx: number) => (
                <tr key={idx} className="hover:bg-[#151D26] transition-colors">
                  <td className="py-2 px-3 text-[#5E6A78]">{tx.timestamp}</td>
                  <td className="py-2 px-3 text-[#B0BAC5]">{tx.sender}</td>
                  <td className="py-2 px-3 text-[#B0BAC5]">{tx.receiver}</td>
                  <td className="py-2 px-3 font-bold text-[#E8EDF2]">₹{tx.amount.toLocaleString()}</td>
                  <td className="py-2 px-3 text-[#5E6A78]">{tx.channel}</td>
                  <td className="py-2 px-3 font-sans">
                    <span className="bg-[#151D26] text-[#B0BAC5] px-2 py-0.5 rounded text-[10px] border border-[#202A35]">
                      {tx.typology}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-bold text-[#EF4444]">{tx.meta_risk_score}%</td>
                  <td className="py-2 px-3 font-sans">
                    {tx.alert_generated ? (
                      <span className="px-2 py-0.5 bg-[#151D26] text-[#EF4444] border border-[#EF4444]/40 rounded text-[10px] font-bold">
                        ALERT ({tx.priority})
                      </span>
                    ) : (
                      <span className="text-[#5E6A78] text-[10px]">PASS</span>
                    )}
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
