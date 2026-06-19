import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useUserProfile, useUpdateProfile } from '@/hooks/useUser'
import { useOrders, useShipmentStatus, Order } from '@/hooks/useOrders'
import { useAuthStore } from '@/store/useAuthStore'
import { formatPrice } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { User, Package, LogOut, Truck, Pencil, Check, X } from 'lucide-react'

// A sub-component to render shipping status for a specific order
const OrderShippingInfo = ({ orderId }: { orderId: string }) => {
  const { data: shipment, isLoading } = useShipmentStatus(orderId)

  if (isLoading) return <Skeleton className="h-4 w-32" />
  if (!shipment) return <span className="text-muted-foreground text-sm">Processing...</span>

  return (
    <div className="flex flex-col gap-1 text-sm mt-2 p-3 bg-muted/50 rounded-md">
      <div className="flex items-center gap-2">
        <Truck className="h-4 w-4 text-primary" />
        <span className="font-semibold text-primary">Shipping Status: {shipment.status}</span>
      </div>
      <div className="text-muted-foreground ml-6">
        Tracking: <span className="font-mono text-foreground">{shipment.tracking_number}</span>
      </div>
      <div className="text-muted-foreground ml-6">
        Est. Delivery: {new Date(shipment.estimated_delivery).toLocaleDateString()}
      </div>
    </div>
  )
}

export default function Profile() {
  const [searchParams] = useSearchParams()
  const defaultTab = searchParams.get('tab') === 'orders' ? 'orders' : 'profile'

  const { logout } = useAuthStore()
  const { data: user, isLoading: isUserLoading } = useUserProfile()
  const { data: orders, isLoading: isOrdersLoading } = useOrders()
  const updateProfile = useUpdateProfile()

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({ full_name: '', phone: '', username: '' })
  const [editError, setEditError] = useState('')
  const [editSuccess, setEditSuccess] = useState(false)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  const startEdit = () => {
    setEditForm({
      full_name: user?.full_name ?? '',
      phone: user?.phone ?? '',
      username: user?.username ?? '',
    })
    setEditError('')
    setEditSuccess(false)
    setIsEditing(true)
  }

  const cancelEdit = () => {
    setIsEditing(false)
    setEditError('')
  }

  const handleSave = async () => {
    setEditError('')
    try {
      await updateProfile.mutateAsync({
        full_name: editForm.full_name || undefined,
        phone: editForm.phone || undefined,
        username: editForm.username || undefined,
      })
      setIsEditing(false)
      setEditSuccess(true)
      setTimeout(() => setEditSuccess(false), 3000)
    } catch (err: any) {
      setEditError(err?.response?.data?.detail || 'Failed to save. Please try again.')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processing': return 'secondary'
      case 'confirmed': return 'default'
      case 'delivered': return 'default'
      case 'cancelled': return 'destructive'
      default: return 'outline'
    }
  }

  return (
    <div className="container py-12 max-w-5xl">
      <h1 className="text-3xl font-extrabold tracking-tight mb-8">My Account</h1>

      <Tabs defaultValue={defaultTab} className="w-full flex flex-col md:flex-row gap-8">
        <TabsList className="flex flex-col h-auto bg-transparent justify-start space-y-2 w-full md:w-64 shrink-0">
          <TabsTrigger
            value="orders"
            className="w-full justify-start px-4 py-3 data-[state=active]:bg-muted data-[state=active]:shadow-none"
          >
            <Package className="mr-2 h-4 w-4" /> Order History
          </TabsTrigger>
          <TabsTrigger
            value="profile"
            className="w-full justify-start px-4 py-3 data-[state=active]:bg-muted data-[state=active]:shadow-none"
          >
            <User className="mr-2 h-4 w-4" /> Profile Details
          </TabsTrigger>
          <div className="w-full pt-4">
            <Button
              variant="ghost"
              className="w-full justify-start text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" /> Logout
            </Button>
          </div>
        </TabsList>

        <div className="flex-1">
          {/* ── Orders tab ── */}
          <TabsContent value="orders" className="m-0 focus-visible:ring-0">
            <Card>
              <CardHeader>
                <CardTitle>Order History</CardTitle>
                <CardDescription>View your past orders and their status.</CardDescription>
              </CardHeader>
              <CardContent>
                {isOrdersLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-32 w-full" />
                    <Skeleton className="h-32 w-full" />
                  </div>
                ) : !orders || orders.length === 0 ? (
                  <div className="text-center py-12 border rounded-lg bg-muted/20">
                    <Package className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium">No orders yet</h3>
                    <p className="text-muted-foreground mt-1">When you place an order, it will appear here.</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {orders.map((order: Order) => (
                      <div key={order.id} className="border rounded-lg p-6">
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 pb-4 border-b">
                          <div>
                            <p className="text-sm text-muted-foreground mb-1">
                              Order Placed: {new Date(order.created_at).toLocaleDateString()}
                            </p>
                            <p className="font-mono font-medium text-sm">ID: {order.id}</p>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <p className="font-bold text-lg">{formatPrice(order.total_price)}</p>
                            <Badge variant={getStatusColor(order.status) as any}>{order.status}</Badge>
                          </div>
                        </div>

                        <div className="space-y-2 mb-4">
                          <p className="text-sm font-medium">Items ({order.items?.length || 0}):</p>
                          {order.items?.map((item) => (
                            <div key={item.id} className="flex justify-between text-sm">
                              <span>Product ID: {item.product_id} ×{item.quantity}</span>
                              <span className="text-muted-foreground">{formatPrice(item.price)}</span>
                            </div>
                          ))}
                        </div>

                        {(order.status === 'PAID' || order.status === 'CONFIRMED' || order.status === 'SHIPPING' || order.status === 'DELIVERED') && (
                          <OrderShippingInfo orderId={order.id} />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── Profile tab ── */}
          <TabsContent value="profile" className="m-0 focus-visible:ring-0">
            <Card>
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle>Profile Details</CardTitle>
                  <CardDescription>Manage your personal information.</CardDescription>
                </div>
                {!isEditing && user && (
                  <Button size="sm" variant="outline" onClick={startEdit}>
                    <Pencil className="mr-2 h-3.5 w-3.5" /> Edit Profile
                  </Button>
                )}
              </CardHeader>
              <CardContent>
                {isUserLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                  </div>
                ) : user ? (
                  isEditing ? (
                    /* ── Edit Form ── */
                    <div className="space-y-4 max-w-md">
                      <div className="space-y-1.5">
                        <Label htmlFor="ef-email">Email</Label>
                        <Input id="ef-email" value={user.email} disabled className="bg-muted/30 text-muted-foreground" />
                        <p className="text-xs text-muted-foreground">Email cannot be changed.</p>
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="ef-name">Full Name</Label>
                        <Input
                          id="ef-name"
                          value={editForm.full_name}
                          onChange={e => setEditForm(f => ({ ...f, full_name: e.target.value }))}
                          placeholder="Your full name"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="ef-username">Username</Label>
                        <Input
                          id="ef-username"
                          value={editForm.username}
                          onChange={e => setEditForm(f => ({ ...f, username: e.target.value }))}
                          placeholder="Your username"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="ef-phone">Phone Number</Label>
                        <Input
                          id="ef-phone"
                          value={editForm.phone}
                          onChange={e => setEditForm(f => ({ ...f, phone: e.target.value }))}
                          placeholder="+84 xxx xxx xxx"
                        />
                      </div>

                      {editError && (
                        <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">{editError}</p>
                      )}

                      <div className="flex gap-2 pt-2">
                        <Button size="sm" onClick={handleSave} disabled={updateProfile.isPending}>
                          <Check className="mr-2 h-3.5 w-3.5" />
                          {updateProfile.isPending ? 'Saving…' : 'Save Changes'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={cancelEdit}>
                          <X className="mr-2 h-3.5 w-3.5" /> Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    /* ── View Mode ── */
                    <div className="space-y-4 max-w-md">
                      {editSuccess && (
                        <div className="text-sm text-green-700 bg-green-100 dark:bg-green-900/20 dark:text-green-400 px-3 py-2 rounded-md border border-green-200 dark:border-green-800">
                          ✓ Profile updated successfully.
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Email</p>
                        <p className="font-medium p-3 bg-muted/30 border rounded-md">{user.email}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Full Name</p>
                        <p className="font-medium p-3 bg-muted/30 border rounded-md">{user.full_name || 'Not set'}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Username</p>
                        <p className="font-medium p-3 bg-muted/30 border rounded-md">@{user.username || 'Not set'}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Phone</p>
                        <p className="font-medium p-3 bg-muted/30 border rounded-md">{user.phone || 'Not set'}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-1">Account Role</p>
                          <Badge variant="secondary" className="capitalize">{user.role || 'customer'}</Badge>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-1">Status</p>
                          <Badge variant={user.is_active ? 'default' : 'destructive'} className="capitalize">
                            {user.status || (user.is_active ? 'Active' : 'Inactive')}
                          </Badge>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Member Since</p>
                        <p className="text-sm text-muted-foreground">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString('vi-VN') : 'N/A'}
                        </p>
                      </div>
                    </div>
                  )
                ) : (
                  <div className="text-destructive p-4 border border-destructive/20 rounded-md bg-destructive/10">
                    Could not load profile information.
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
