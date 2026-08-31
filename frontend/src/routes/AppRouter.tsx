import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppLayout } from '@/components/layout/AppLayout'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { PlaceholderPage } from '@/pages/PlaceholderPage'
import { CustomersPage } from '@/pages/customers/CustomersPage'
import { CustomerDetailPage } from '@/pages/customers/CustomerDetailPage'
import { GuestRoute } from '@/routes/GuestRoute'
import { ProtectedRoute } from '@/routes/ProtectedRoute'

export const router = createBrowserRouter([
  {
    element: <GuestRoute><LoginPage /></GuestRoute>,
    path: '/login',
  },
  {
    element: <GuestRoute><ForgotPasswordPage /></GuestRoute>,
    path: '/forgot-password',
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'customers', element: <CustomersPage /> },
          { path: 'customers/:customerId', element: <CustomerDetailPage /> },
          {
            path: 'transactions',
            element: (
              <PlaceholderPage
                title="Transactions"
                description="Review transaction activity and risk signals."
              />
            ),
          },
          {
            path: 'cases',
            element: (
              <PlaceholderPage
                title="Cases"
                description="Investigate and resolve operational cases."
              />
            ),
          },
          {
            path: 'alerts',
            element: (
              <PlaceholderPage
                title="Alerts"
                description="Triage and resolve alert workflows."
              />
            ),
          },
          {
            path: 'reports',
            element: (
              <PlaceholderPage
                title="Reports"
                description="Export operational and SLA performance reports."
              />
            ),
          },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])
