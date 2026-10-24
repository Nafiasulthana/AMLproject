import React from 'react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area 
} from 'recharts';

interface RiskChartsProps {
  riskDist: Array<{ level: string; count: number; color: string }>;
  typologyDist: Array<{ typology: string; count: number }>;
  volumeTrend: Array<{ time: string; volume: number }>;
}

export const RiskCharts: React.FC<RiskChartsProps> = ({ riskDist, typologyDist, volumeTrend }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5 select-none">
      {/* Risk Distribution Pie Chart */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4">
        <div className="flex items-center justify-between mb-3 border-b border-[#202A35] pb-2">
          <span className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider">
            Risk Distribution
          </span>
          <span className="text-[10px] text-[#3B82F6] font-mono font-semibold">HYBRID RISK ENGINE</span>
        </div>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={riskDist}
                dataKey="count"
                nameKey="level"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={75}
                paddingAngle={3}
              >
                {riskDist.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#151D26', borderColor: '#202A35', borderRadius: '4px', color: '#E8EDF2', fontSize: '11px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-center space-x-3 mt-1">
          {riskDist.map((item, i) => (
            <div key={i} className="flex items-center space-x-1 text-[11px] font-mono">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></span>
              <span className="text-[#8995A3]">{item.level} ({item.count})</span>
            </div>
          ))}
        </div>
      </div>

      {/* Typology Breakdown Bar Chart */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4">
        <div className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-3 border-b border-[#202A35] pb-2">
          Detected Typologies Breakdown
        </div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={typologyDist}>
              <CartesianGrid strokeDasharray="2 2" stroke="#202A35" vertical={false} />
              <XAxis dataKey="typology" stroke="#5E6A78" fontSize={9} tickLine={false} />
              <YAxis stroke="#5E6A78" fontSize={9} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#151D26', borderColor: '#202A35', color: '#E8EDF2', fontSize: '11px' }} />
              <Bar dataKey="count" fill="#3B82F6" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Intraday Money Velocity Area Chart */}
      <div className="bg-[#111820] border border-[#202A35] rounded-lg p-4">
        <div className="text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-3 border-b border-[#202A35] pb-2">
          Suspicious Activity Trend
        </div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={volumeTrend}>
              <defs>
                <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 2" stroke="#202A35" vertical={false} />
              <XAxis dataKey="time" stroke="#5E6A78" fontSize={9} />
              <YAxis stroke="#5E6A78" fontSize={9} tickFormatter={(val) => `₹${val/100000}L`} />
              <Tooltip contentStyle={{ backgroundColor: '#151D26', borderColor: '#202A35', color: '#E8EDF2', fontSize: '11px' }} />
              <Area type="monotone" dataKey="volume" stroke="#3B82F6" strokeWidth={1.5} fillOpacity={1} fill="url(#colorVol)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
