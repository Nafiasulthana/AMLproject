import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  LayoutDashboard, 
  Cpu, 
  AlertTriangle, 
  Search, 
  Network, 
  GitCommit, 
  FolderLock, 
  FileText, 
  Sliders
} from 'lucide-react';

interface NavSection {
  title: string;
  items: Array<{
    name: string;
    path: string;
    icon: React.ElementType;
    roles: string[];
  }>;
}

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role || 'INVESTIGATOR';

  const sections: NavSection[] = [
    {
      title: 'MONITOR',
      items: [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER', 'ANALYST'] },
        { name: 'Alert Queue', path: '/alerts', icon: AlertTriangle, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER', 'ANALYST'] },
      ]
    },
    {
      title: 'INVESTIGATE',
      items: [
        { name: 'Investigation Workspace', path: '/investigation', icon: Search, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER'] },
        { name: 'Graph Explorer', path: '/graph', icon: Network, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER', 'ANALYST'] },
        { name: 'Fund Flow', path: '/fund-flow', icon: GitCommit, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER'] },
      ]
    },
    {
      title: 'CASES',
      items: [
        { name: 'Case Management', path: '/cases', icon: FolderLock, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER'] },
        { name: 'STR Reports', path: '/str-reports', icon: FileText, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER'] },
      ]
    },
    {
      title: 'OPERATIONS',
      items: [
        { name: 'Transaction Simulator', path: '/simulator', icon: Cpu, roles: ['ADMIN', 'INVESTIGATOR', 'OFFICER', 'ANALYST'] },
      ]
    },
    {
      title: 'ADMINISTRATION',
      items: [
        { name: 'Admin Panel', path: '/admin', icon: Sliders, roles: ['ADMIN', 'OFFICER'] },
      ]
    }
  ];

  return (
    <aside className="w-60 bg-[#111820] border-r border-[#202A35] flex flex-col justify-between min-h-[calc(100vh-3.5rem)] select-none shrink-0">
      <div className="py-4 px-3 space-y-5">
        {sections.map((sec) => {
          const visibleItems = sec.items.filter(item => item.roles.includes(role));
          if (visibleItems.length === 0) return null;

          return (
            <div key={sec.title} className="space-y-1">
              <div className="px-2 pb-1.5 text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider">
                {sec.title}
              </div>
              {visibleItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center space-x-2.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-[#151D26] text-[#3B82F6] border-l-2 border-[#3B82F6] font-semibold pl-2 font-sans'
                          : 'text-[#8995A3] hover:text-[#E8EDF2] hover:bg-[#151D26]/60'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* System Status Footer */}
      <div className="p-3 m-3 bg-[#0B0F14] rounded border border-[#202A35]">
        <div className="text-[11px] font-medium text-[#B0BAC5] flex items-center justify-between">
          <span>Graph & ML Engine</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]"></span>
        </div>
        <div className="text-[10px] text-[#5E6A78] font-mono mt-0.5">
          XGBoost + Cypher Active
        </div>
      </div>
    </aside>
  );
};
