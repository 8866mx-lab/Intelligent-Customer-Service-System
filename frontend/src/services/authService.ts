import api from './api';
import type { ApiResponse, LoginRequest, LoginResponse, User } from '@/types/auth';
import { mockLogin, mockGetMe, mockLogout } from '@/mocks/auth';

const useMock = import.meta.env.VITE_USE_MOCK === 'true';

export const authService = {
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    if (useMock) {
      return mockLogin(credentials);
    }
    const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', credentials);
    return response.data;
  },

  async logout(): Promise<ApiResponse<null>> {
    if (useMock) {
      return mockLogout();
    }
    const response = await api.post<ApiResponse<null>>('/auth/logout');
    return response.data;
  },

  async getMe(): Promise<ApiResponse<User>> {
    if (useMock) {
      return mockGetMe();
    }
    const response = await api.get<ApiResponse<User>>('/auth/me');
    return response.data;
  },
};
