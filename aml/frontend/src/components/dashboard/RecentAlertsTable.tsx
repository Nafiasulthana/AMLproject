import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowRight } from 'lucide-react';

interface RecentAlertsProps {
  alerts: Array<{
    alert_id: string;
    customer_id: string;
    typology: string;
    meta_risk_score: number;
    priority: string;
    status: string;
    created_at: string;
  }>;
}

export const RecentAlertsTable: React.FC<RecentAlertsProps> = ({ alerts }) => {
  const navigate = useNavigate();

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'CRITICAL': return 'text-[#EF4444] bg-[#EF4444]/10 border-[#EF4444]/40';
      case 'HIGH': return 'text-[#F59E0B] bg-[#F59E0B]/10 border-[#F59E0B]/40';
      case 'MEDIUM': return 'text-[#3B82F6] bg-[#3B82F6]/10 border-[#3B82F6]/40';
      default: return 'text-[#22C55E] bg-[#22C55E]/10 border-[#22C55E]/40';
    }
  };

  return (
    <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4 select-none">
      <div className="flex items-center justify-between mb-3 border-b border-[#202A35] pb-2">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-[#3B82F6]" />
          <h3 className="text-xs font-bold text-[#E8EDF2] uppercase tracking-wider">
            Real-Time Suspicious Alert Stream
          </h3>
        </div>
        <button 
          onClick={() => navigate('/alerts')}
          className="text-xs text-[#3B82F6] hover:underline flex items-center space-x-1 font-medium"
        >
          <span>View Full Queue</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#202A35] text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider">
              <th className="py-2 px-3">Alert ID</th>
              <th className="py-2 px-3">Customer</th>
              <th className="py-2 px-3">Typology</th>
              <th className="py-2 px-3">Meta Risk</th>
              <th className="py-2 px-3">Priority</th>
              <th className="py-2 px-3">Status</th>
              <th className="py-2 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#202A35]/60 font-mono text-[#E8EDF2]">
            {alerts.map((alert) => (
              <tr key={alert.alert_id} className="hover:bg-[#151D26] transition-colors">
                <td className="py-2 px-3 text-[#3B82F6] font-semibold">{alert.alert_id}</td>
                <td className="py-2 px-3 text-[#B0BAC5]">{alert.customer_id}</td>
                <td className="py-2 px-3">
                  <span className="bg-[#151D26] text-[#B0BAC5] px-2 py-0.5 rounded text-[11px] font-sans border border-[#202A35]">
                    {alert.typology}
                  </span>
                </td>
                <td className="py-2 px-3 font-bold text-[#E8EDF2]">{alert.meta_risk_score}%</td>
                <td className="py-2 px-3 font-sans">
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getPriorityBadge(alert.priority)}`}>
                    {alert.priority}
                  </span>
                </td>
                <td className="py-2 px-3 font-sans text-[11px] text-[#8995A3]">
                  {alert.status}
                </td>
                <td className="py-2 px-3 text-right font-sans">
                  <button 
                    onClick={() => navigate(`/investigation?alert=${alert.alert_id}`)}
                    className="px-2.5 py-1 bg-[#151D26] text-[#3B82F6] border border-[#202A35] hover:border-[#3B82F6]/50 rounded text-[11px] font-medium transition-colors"
                  >
                    Investigate
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
