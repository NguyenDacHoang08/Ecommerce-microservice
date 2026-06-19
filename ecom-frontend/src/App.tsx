import { Routes, Route } from 'react-router-dom'
import MainLayout from '@/components/layout/MainLayout'
import Home from '@/pages/Home'
import Login from '@/pages/auth/Login'
import Register from '@/pages/auth/Register'
import NotAuthorized from '@/pages/NotAuthorized'
import ProtectedRoute from '@/routes/ProtectedRoute'
import AdminRoute from '@/routes/AdminRoute'
import ProductList from '@/pages/products/ProductList'
import ProductDetail from '@/pages/products/ProductDetail'
import Recommendations from '@/pages/products/Recommendations'
import Cart from '@/pages/cart/Cart'
import Checkout from '@/pages/checkout/Checkout'
import OrderSuccess from '@/pages/checkout/OrderSuccess'
import Profile from '@/pages/profile/Profile'
import DashboardLayout from '@/pages/dashboard/DashboardLayout'
import DashboardOverview from '@/pages/dashboard/DashboardOverview'
import DashboardOrders from '@/pages/dashboard/DashboardOrders'
import DashboardUsers from '@/pages/dashboard/DashboardUsers'
import DashboardProducts from '@/pages/dashboard/DashboardProducts'
import DashboardShipping from '@/pages/dashboard/DashboardShipping'

function App() {
  return (
    <Routes>
      {/* Auth Routes - No Layout */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* 403 - No Layout */}
      <Route path="/403" element={<NotAuthorized />} />

      {/* Admin/Staff Dashboard Routes */}
      <Route element={<AdminRoute allowedRoles={['admin', 'staff']} />}>
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<DashboardOverview />} />
          <Route path="orders" element={<DashboardOrders />} />
          <Route path="products" element={<DashboardProducts />} />
          <Route path="shipping" element={<DashboardShipping />} />
          {/* Users - Admin only */}
          <Route element={<AdminRoute allowedRoles={['admin']} />}>
            <Route path="users" element={<DashboardUsers />} />
          </Route>
        </Route>
      </Route>

      {/* Main Layout Routes */}
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Home />} />
        <Route path="products" element={<ProductList />} />
        <Route path="products/:id" element={<ProductDetail />} />
        <Route path="recommendations" element={<Recommendations />} />
        
        {/* Protected Routes inside Layout */}
        <Route element={<ProtectedRoute />}>
          <Route path="cart" element={<Cart />} />
          <Route path="checkout" element={<Checkout />} />
          <Route path="checkout/success" element={<OrderSuccess />} />
          <Route path="profile" element={<Profile />} />
        </Route>
      </Route>
    </Routes>
  )
}

export default App
