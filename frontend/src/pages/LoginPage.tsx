import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message } from 'antd';
import { useAuthStore } from '@/stores/useAuthStore';
import { authService } from '@/services/authService';
import './LoginPage.css';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/employee', { replace: true });
    }
  }, [navigate]);

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const response = await authService.login(values);
      if (response.code === 200 && response.data) {
        setAuth(response.data.user, response.data.access_token);
        message.success('登录成功');
        navigate('/employee');
      } else {
        message.error(response.message || '登录失败');
      }
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number; data?: { code?: number } } };
        if (axiosError.response?.status === 401 && axiosError.response?.data?.code === 1001) {
          message.error('用户名或密码错误');
        } else {
          message.error('登录失败，请稍后重试');
        }
      } else {
        message.error('登录失败，请稍后重试');
      }
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <Card className="login-card">
        <h1 className="login-title">智能客服系统</h1>
        <p className="login-subtitle">企业内部智能问答与人工客服平台</p>
        <Form
          name="login"
          initialValues={{ username: 'zhangsan', password: 'password123' }}
          onFinish={handleLogin}
          layout="vertical"
          requiredMark={false}
          size="large"
        >
          <Form.Item
            label="账号"
            name="username"
            rules={[{ required: true, message: '请输入账号' }]}
          >
            <Input placeholder="请输入账号" />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" block loading={loading} style={{ height: 40 }}>
              登 录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};
