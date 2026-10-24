import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

interface User {
  user_id: string;
  username: string;
  full_name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  switchRoleDemo: (role: string) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('aml_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (token) {
      api.get('/auth/me')
        .then((res) => {
          setUser({
            user_id: res.data.user_id,
            username: res.data.username,
            full_name: res.data.full_name,
            role: res.data.role_id || res.data.role
          });
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (username: string, password: string) => {
    const res = await api.post('/auth/login', { username, password });
    const newToken = res.data.access_token;
    localStorage.setItem('aml_token', newToken);
    setToken(newToken);
    setUser({
      user_id: res.data.user_id,
      username: res.data.username,
      full_name: res.data.full_name,
      role: res.data.role
    });
  };

  const switchRoleDemo = (role: string) => {
    const roleUserMap: Record<string, { u: string; p: string }> = {
      'ADMIN': { u: 'admin', p: 'admin123' },
      'INVESTIGATOR': { u: 'investigator', p: 'inv123' },
      'OFFICER': { u: 'officer', p: 'officer123' },
      'ANALYST': { u: 'analyst', p: 'analyst123' }
    };
    const creds = roleUserMap[role] || roleUserMap['INVESTIGATOR'];
    login(creds.u, creds.p);
  };

  const logout = () => {
    localStorage.removeItem('aml_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, switchRoleDemo, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
