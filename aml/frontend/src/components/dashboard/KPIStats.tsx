import React from 'react';
import { ShieldAlert, AlertOctagon, FolderKanban, Users, Activity, CheckCircle2 } from 'lucide-react';

interface KPIProps {
  data: {
    transactions_today: number;
    alerts_today: number;
    critical_alerts: number;
    open_cases: number;
    closed_cases: number;
    high_risk_customers: number;
  };
}

export const KPIStats: React.FC<KPIProps> = ({ data }) => {
  const kpis = [
    { label: 'Active Alerts', value: data.alerts_today, icon: ShieldAlert, highlight: 'text-[#3B82F6]' },
    { label: 'Critical Alerts', value: data.critical_alerts, icon: AlertOctagon, highlight: 'text-[#EF4444]' },
    { label: 'High-Risk Accounts', value: data.high_risk_customers, icon: Users, highlight: 'text-[#F59E0B]' },
    { label: 'Open Cases', value: data.open_cases, icon: FolderKanban, highlight: 'text-[#E8EDF2]' },
    { label: 'Suspicious Flow', value: `₹${((data.transactions_today * 450) / 1000).toFixed(1)}k`, icon: Activity, highlight: 'text-[#E8EDF2]' },
    { label: 'Closed Cases', value: data.closed_cases, icon: CheckCircle2, highlight: 'text-[#22C55E]' },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-5 select-none">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon;
        return (
          <div key={idx} className="bg-[#111820] border border-[#202A35] rounded p-3 text-left">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider">{kpi.label}</span>
              <Icon className="w-3.5 h-3.5 text-[#5E6A78]" />
            </div>
            <div className={`text-xl font-bold font-mono tracking-tight ${kpi.highlight}`}>
              {typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
            </div>
          </div>
        );
      })}
    </div>
  );
};
