import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/useAuthStore'
import {
  LayoutDashboard, Users, ShoppingBag, Package,
  LogOut, Home, Truck
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const DashboardLayout = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }


  const navItems = [
    {
      to: '/dashboard',
      icon: LayoutDashboard,
      label: 'Overview',
      end: true,
      roles: ['admin', 'staff'],
    },
    {
      to: '/dashboard/orders',
      icon: ShoppingBag,
      label: 'Orders',
      roles: ['admin', 'staff'],
    },
    {
      to: '/dashboard/products',
      icon: Package,
      label: 'Products',
      roles: ['admin', 'staff'],
    },
    {
      to: '/dashboard/shipping',
      icon: Truck,
      label: 'Shipping',
      roles: ['admin', 'staff'],
    },
    {
      to: '/dashboard/users',
      icon: Users,
      label: 'Users',
      roles: ['admin'],
    },
  ].filter(item => item.roles.includes(user?.role || ''))

  return (
    <div className="flex min-h-screen bg-muted/20">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r bg-background flex flex-col">
        {/* Logo / Branding */}
        <div className="p-6 border-b">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <LayoutDashboard className="h-4 w-4 text-primary-foreground" />
            </div>
            <div>
              <p className="font-bold text-sm">MicroEcom</p>
              <p className="text-xs text-muted-foreground capitalize">{user?.role} Panel</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div className="p-4 border-b bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-primary/10 border flex items-center justify-center">
              <span className="text-sm font-bold text-primary">
                {(user?.full_name || user?.email || 'A')[0].toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name || user?.email}</p>
              <Badge variant="secondary" className="text-xs capitalize mt-0.5">{user?.role}</Badge>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t space-y-1">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-muted-foreground hover:text-foreground"
            asChild
          >
            <a href="/">
              <Home className="mr-2 h-4 w-4" /> Back to Store
            </a>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-destructive hover:bg-destructive/10 hover:text-destructive"
            onClick={handleLogout}
          >
            <LogOut className="mr-2 h-4 w-4" /> Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

export default DashboardLayout
