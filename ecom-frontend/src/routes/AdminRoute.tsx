import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/useAuthStore'

interface AdminRouteProps {
  allowedRoles?: ('admin' | 'staff' | 'customer')[]
}

const AdminRoute = ({ allowedRoles = ['admin', 'staff'] }: AdminRouteProps) => {
  const { isAuthenticated, user } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (!user || !allowedRoles.includes(user.role as any)) {
    return <Navigate to="/403" replace />
  }

  return <Outlet />
}

export default AdminRoute
