import { createBrowserRouter, Navigate } from 'react-router-dom'

import { AppLayout } from '@/components/layout/AppLayout'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { AlertDetailPage } from '@/pages/alerts/AlertDetailPage'
import { AlertsPage } from '@/pages/alerts/AlertsPage'
import { CaseDetailPage } from '@/pages/cases/CaseDetailPage'
import { CasesPage } from '@/pages/cases/CasesPage'
import { CustomerDetailPage } from '@/pages/customers/CustomerDetailPage'
import { CustomersPage } from '@/pages/customers/CustomersPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ReportDetailPage } from '@/pages/reports/ReportDetailPage'
import { ReportsPage } from '@/pages/reports/ReportsPage'
import { TransactionDetailPage } from '@/pages/transactions/TransactionDetailPage'
import { TransactionsPage } from '@/pages/transactions/TransactionsPage'
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
          { path: 'transactions', element: <TransactionsPage /> },
          { path: 'transactions/:transactionId', element: <TransactionDetailPage /> },
          { path: 'cases', element: <CasesPage /> },
          { path: 'cases/:caseId', element: <CaseDetailPage /> },
          { path: 'alerts', element: <AlertsPage /> },
          { path: 'alerts/:alertId', element: <AlertDetailPage /> },
          { path: 'reports', element: <ReportsPage /> },
          { path: 'reports/:reportType', element: <ReportDetailPage /> },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])
