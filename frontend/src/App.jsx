import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import SubmitComplaint from './pages/SubmitComplaint'
import CasesList from './pages/CasesList'
import CaseDetail from './pages/CaseDetail'
import Notifications from './pages/Notifications'
import Institutions from './pages/Institutions'
import Coordination from './pages/Coordination'
import Reports from './pages/Reports'
import UsersAdmin from './pages/UsersAdmin'
import Bureaus from './pages/Bureaus'
import Analytics from './pages/Analytics'
import NotFound from './pages/NotFound'
import Loading from './components/Loading'

function PrivateRoute({ children, roles }) {
  const { user, loading, isAuthenticated } = useAuth()
  if (loading) return <Loading />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <Loading text="Initializing INSTITRACK..." />

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />

      <Route
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/submit" element={<PrivateRoute roles={['complainant', 'super_admin']}><SubmitComplaint /></PrivateRoute>} />
        <Route path="/cases" element={<CasesList />} />
        <Route path="/cases/:id" element={<CaseDetail />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/institutions" element={<PrivateRoute roles={['central_monitoring', 'super_admin', 'auditor']}><Institutions /></PrivateRoute>} />
        <Route path="/coordination" element={<PrivateRoute roles={['bureau_officer', 'central_monitoring', 'super_admin']}><Coordination /></PrivateRoute>} />
        <Route path="/reports" element={<PrivateRoute roles={['central_monitoring', 'super_admin', 'auditor', 'bureau_officer']}><Reports /></PrivateRoute>} />
        <Route path="/audit" element={<PrivateRoute roles={['auditor', 'super_admin', 'central_monitoring']}><Reports /></PrivateRoute>} />
        <Route path="/users" element={<PrivateRoute roles={['super_admin']}><UsersAdmin /></PrivateRoute>} />
        <Route path="/bureaus" element={<PrivateRoute roles={['super_admin']}><Bureaus /></PrivateRoute>} />
        <Route path="/analytics" element={<PrivateRoute roles={['central_monitoring', 'super_admin', 'auditor']}><Analytics /></PrivateRoute>} />
      </Route>

      <Route path="/" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
