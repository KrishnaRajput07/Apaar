import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { User, UserRole } from '@/types';
import { authApi } from '@/lib/api';

interface AuthContextValue {
  user: User | null;
  login: (role: UserRole) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

// Fallback mock users for when backend is not running
const FALLBACK_USERS: Record<UserRole, User> = {
  student: {
    id: 'STU-001', name: 'Arjun Sharma', email: 'arjun@demo.edu',
    role: 'student', avatarInitials: 'AS',
  },
  institution: {
    id: 'INST-ADM-001', name: 'Dr. Priya Nair', email: 'admin@demo.edu',
    role: 'institution', institutionId: 'INST-MH-0042',
    institutionName: 'Demo Institute of Technology, Mumbai', avatarInitials: 'PN',
  },
  officer: {
    id: 'OFCR-001', name: 'Shri Rajesh Kumar', email: 'officer@aicte.gov',
    role: 'officer', avatarInitials: 'RK',
  },
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    // Try to restore from localStorage
    const saved = localStorage.getItem('apaar_user');
    if (saved) {
      try { return JSON.parse(saved); } catch { return null; }
    }
    return null;
  });

  const login = useCallback(async (role: UserRole) => {
    // Try real backend first
    try {
      const { data } = await authApi.demoLogin(role);
      localStorage.setItem('apaar_token', data.access_token);
      const u: User = {
        id: data.user.id,
        name: data.user.name,
        email: data.user.email,
        role: data.user.role as UserRole,
        institutionId: data.user.institution_id,
        avatarInitials: data.user.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase(),
      };
      localStorage.setItem('apaar_user', JSON.stringify(u));
      setUser(u);
    } catch {
      // Fallback to mock if backend not running
      const fallback = FALLBACK_USERS[role];
      localStorage.setItem('apaar_user', JSON.stringify(fallback));
      setUser(fallback);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('apaar_token');
    localStorage.removeItem('apaar_user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
