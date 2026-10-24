import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { KPIStats } from '../components/dashboard/KPIStats';
import { RiskCharts } from '../components/dashboard/RiskCharts';
import { RecentAlertsTable } from '../components/dashboard/RecentAlertsTable';
import { ShieldCheck, RefreshCw } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = () => {
    setLoading(true);
    api.get('/dashboard/metrics')
      .then(res => setData(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return <div className="p-8 text-center text-[#8995A3] text-xs font-mono">Querying AML Surveillance Engine Telemetry...</div>;
  }

  return (
    <div className="space-y-5 select-none">
      <div className="flex items-center justify-between border-b border-[#202A35] pb-3">
        <div>
          <h1 className="text-sm font-bold text-[#E8EDF2] tracking-tight flex items-center space-x-2">
            <span>AML Surveillance & Operations Monitoring</span>
            <ShieldCheck className="w-4 h-4 text-[#3B82F6]" />
          </h1>
          <p className="text-[11px] text-[#8995A3] mt-0.5">Real-time banking transaction surveillance, graph topology, and hybrid ML risk scoring</p>
        </div>

        <button 
          onClick={fetchDashboard}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#111820] border border-[#202A35] text-[#8995A3] hover:text-[#E8EDF2] rounded text-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {data && (
        <>
          <KPIStats data={data} />
          <RiskCharts 
            riskDist={data.risk_distribution}
            typologyDist={data.typology_distribution}
            volumeTrend={data.volume_trend}
          />
          <RecentAlertsTable alerts={data.recent_alerts} />
        </>
      )}
    </div>
  );
};
