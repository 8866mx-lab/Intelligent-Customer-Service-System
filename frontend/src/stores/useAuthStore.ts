import { create } from 'zustand';
import type { User } from '@/types/auth';
import { authService } from '@/services/authService';

interface AuthState {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  loadAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  setAuth: (user, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    set({ user, token });
  },
  clearAuth: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ user: null, token: null });
  },
  loadAuth: async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await authService.getMe();
        if (response.code === 200 && response.data) {
          set({ user: response.data, token });
          localStorage.setItem('user', JSON.stringify(response.data));
        } else {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          set({ user: null, token: null });
        }
      } catch (e) {
        console.error('Failed to validate token', e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        set({ user: null, token: null });
      }
    }
  },
}));
