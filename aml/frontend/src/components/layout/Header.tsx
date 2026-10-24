import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { Shield, Play, Pause, Activity, User as UserIcon, LogOut, ChevronDown } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, switchRoleDemo, logout } = useAuth();
  const [simRunning, setSimRunning] = useState(false);

  useEffect(() => {
    const checkSim = () => {
      api.get('/simulation/status')
        .then(res => setSimRunning(res.data.is_running && !res.data.is_paused))
        .catch(() => {});
    };
    checkSim();
    const interval = setInterval(checkSim, 3000);
    return () => clearInterval(interval);
  }, []);

  const toggleSim = async () => {
    if (simRunning) {
      await api.post('/simulation/pause');
      setSimRunning(false);
    } else {
      await api.post('/simulation/start');
      setSimRunning(true);
    }
  };

  return (
    <header className="h-14 bg-[#111820] border-b border-[#202A35] px-5 flex items-center justify-between sticky top-0 z-40 select-none">
      {/* Platform Branding */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded bg-[#151D26] border border-[#202A35] flex items-center justify-center text-[#3B82F6]">
          <Shield className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-sm tracking-tight text-[#E8EDF2]">AMLSentinel</span>
            <span className="text-[10px] text-[#8995A3] font-mono border-l border-[#202A35] pl-2 uppercase tracking-wider">
              AML INVESTIGATION PLATFORM
            </span>
          </div>
        </div>
      </div>

      {/* Action Controls & User Identity */}
      <div className="flex items-center space-x-4">
        {/* Live Simulator Status Badge / Action */}
        <button
          onClick={toggleSim}
          className={`flex items-center space-x-2 px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
            simRunning 
              ? 'bg-[#151D26] text-[#22C55E] border-[#22C55E]/40'
              : 'bg-[#151D26] text-[#8995A3] border-[#202A35] hover:text-[#E8EDF2]'
          }`}
          title="Toggle Simulation Stream"
        >
          <Activity className={`w-3.5 h-3.5 ${simRunning ? 'text-[#22C55E]' : 'text-[#5E6A78]'}`} />
          <span className="font-mono text-[11px]">SIMULATOR: {simRunning ? 'RUNNING' : 'STOPPED'}</span>
          {simRunning ? <Pause className="w-3.5 h-3.5 text-[#22C55E]" /> : <Play className="w-3.5 h-3.5" />}
        </button>

        {/* Demo Role Switcher */}
        <div className="flex items-center space-x-1.5 bg-[#151D26] border border-[#202A35] px-2.5 py-1 rounded text-xs">
          <span className="text-[11px] text-[#5E6A78]">Role:</span>
          <select
            value={user?.role || 'INVESTIGATOR'}
            onChange={(e) => switchRoleDemo(e.target.value)}
            className="bg-transparent text-xs text-[#3B82F6] font-medium focus:outline-none cursor-pointer pr-1"
          >
            <option value="ADMIN" className="bg-[#111820] text-[#E8EDF2]">Admin</option>
            <option value="INVESTIGATOR" className="bg-[#111820] text-[#E8EDF2]">Investigator</option>
            <option value="OFFICER" className="bg-[#111820] text-[#E8EDF2]">Officer</option>
            <option value="ANALYST" className="bg-[#111820] text-[#E8EDF2]">Analyst</option>
          </select>
        </div>

        {/* User Identity & Logout */}
        <div className="flex items-center space-x-3 border-l border-[#202A35] pl-4">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-semibold text-[#E8EDF2]">{user?.full_name || 'Investigator'}</div>
            <div className="text-[10px] text-[#8995A3] font-mono">{user?.role || 'INVESTIGATOR'}</div>
          </div>
          <button 
            onClick={logout}
            className="p-1.5 text-[#8995A3] hover:text-[#EF4444] transition-colors rounded hover:bg-[#151D26]"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
