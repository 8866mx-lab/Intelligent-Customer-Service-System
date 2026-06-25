import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Dropdown, type MenuProps } from 'antd';
import { useAuthStore } from '@/stores/useAuthStore';
import { authService } from '@/services/authService';
import './AppShell.css';

export const AppShell: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearAuth } = useAuthStore();

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      navigate('/login');
    }
  };

  const items: MenuProps['items'] = [
    {
      key: 'logout',
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const navItems = [
    { key: '/employee', label: '员工端' },
    { key: '/agent', label: '坐席端' },
    { key: '/knowledge', label: '知识库' },
  ];

  return (
    <div className="shell">
      <header className="shell-header">
        <div className="shell-logo">智能客服</div>
        <nav className="shell-nav">
          {navItems.map(item => (
            <a
              key={item.key}
              href={item.key}
              className={location.pathname === item.key ? 'active' : ''}
              onClick={(e) => {
                e.preventDefault();
                navigate(item.key);
              }}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <Dropdown menu={{ items }} placement="bottomRight">
          <div className="shell-user">{user?.username || '用户'} ▼</div>
        </Dropdown>
      </header>

      <div className="shell-body">
        <Outlet />
      </div>
    </div>
  );
};
