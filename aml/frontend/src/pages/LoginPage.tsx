import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, User, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { user, token, login, switchRoleDemo } = useAuth();
  const [username, setUsername] = useState('investigator');
  const [password, setPassword] = useState('inv123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (token && user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center p-6 select-none font-sans">
      <div className="max-w-sm w-full bg-[#111820] border border-[#202A35] rounded-lg p-6 shadow-xl">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded bg-[#151D26] border border-[#202A35] text-[#3B82F6] mb-3">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="text-base font-bold text-[#E8EDF2] tracking-tight">AMLSentinel Platform</h1>
          <p className="text-xs text-[#8995A3] mt-0.5">Financial Intelligence & AML Investigation Workstation</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-[#151D26] border border-[#EF4444]/60 rounded text-[#EF4444] text-xs flex items-center space-x-2">
            <Shield className="w-4 h-4 shrink-0 text-[#EF4444]" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-1">Username</label>
            <div className="relative">
              <User className="w-3.5 h-3.5 text-[#5E6A78] absolute left-3 top-2.5" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full bg-[#151D26] border border-[#202A35] rounded pl-9 pr-3 py-1.5 text-xs text-[#E8EDF2] focus:outline-none focus:border-[#3B82F6]"
                placeholder="User ID"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-[#8995A3] uppercase tracking-wider mb-1">Password</label>
            <div className="relative">
              <Lock className="w-3.5 h-3.5 text-[#5E6A78] absolute left-3 top-2.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-[#151D26] border border-[#202A35] rounded pl-9 pr-3 py-1.5 text-xs text-[#E8EDF2] focus:outline-none focus:border-[#3B82F6]"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-[#3B82F6] hover:bg-[#2563EB] text-white font-semibold text-xs rounded transition-colors flex items-center justify-center space-x-1.5"
          >
            <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Quick Role Switcher */}
        <div className="mt-6 pt-4 border-t border-[#202A35]">
          <div className="text-[10px] font-bold text-[#5E6A78] uppercase tracking-wider mb-2 text-center">
            Demo Roles Quick Login
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { role: 'INVESTIGATOR', label: 'Investigator' },
              { role: 'ADMIN', label: 'Admin' },
              { role: 'OFFICER', label: 'Officer' },
              { role: 'ANALYST', label: 'Analyst' }
            ].map((r) => (
              <button
                key={r.role}
                type="button"
                onClick={() => switchRoleDemo(r.role)}
                className="p-1.5 bg-[#151D26] border border-[#202A35] hover:border-[#3B82F6]/50 rounded text-[11px] text-[#8995A3] hover:text-[#E8EDF2] font-medium transition-colors text-center"
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
