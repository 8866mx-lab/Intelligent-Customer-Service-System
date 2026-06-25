import type { ApiResponse, LoginRequest, LoginResponse, User } from '@/types/auth';

export const mockLogin = async (credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));

  if (credentials.username === 'zhangsan' && credentials.password === 'password123') {
    return {
      code: 200,
      message: 'success',
      data: {
        access_token: 'mock-token-' + Date.now(),
        token_type: 'bearer',
        expires_in: 86400,
        user: {
          id: 1,
          username: 'zhangsan',
        },
      },
    };
  }

  return {
    code: 1001,
    message: '用户名或密码错误',
    data: null,
  };
};

export const mockLogout = async (): Promise<ApiResponse<null>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return {
    code: 200,
    message: 'success',
    data: null,
  };
};

export const mockGetMe = async (): Promise<ApiResponse<User>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      return {
        code: 200,
        message: 'success',
        data: user,
      };
    } catch (e) {
      console.error('Failed to parse user', e);
    }
  }

  return {
    code: 1002,
    message: 'Token 已过期或无效',
    data: null,
  };
};
