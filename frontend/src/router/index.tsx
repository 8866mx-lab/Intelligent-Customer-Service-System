import { Navigate, createBrowserRouter } from 'react-router-dom';
import { AppShell } from '@/components/AppShell';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { LoginPage } from '@/pages/LoginPage';
import { EmployeePage } from '@/pages/EmployeePage';
import { AgentPage } from '@/pages/AgentPage';
import { KnowledgePage } from '@/pages/KnowledgePage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/employee" replace />,
      },
      {
        path: 'employee',
        element: <EmployeePage />,
      },
      {
        path: 'agent',
        element: <AgentPage />,
      },
      {
        path: 'knowledge',
        element: <KnowledgePage />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/login" replace />,
  },
]);
