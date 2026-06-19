import { useState } from 'react'
import { useAdminOrders, useUpdateOrderStatus, useDeleteOrder } from '@/hooks/useAdmin'
import { formatPrice } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { Filter, RefreshCw, Trash2 } from 'lucide-react'

const STATUS_OPTIONS = ['ALL', 'PROCESSING', 'CONFIRMED', 'CANCELLED', 'DELIVERED']

const statusColors: Record<string, string> = {
  PROCESSING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
  CONFIRMED: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  CANCELLED: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  DELIVERED: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
}

export default function DashboardOrders() {
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const { data: orders, isLoading, refetch } = useAdminOrders(
    statusFilter !== 'ALL' ? statusFilter : undefined
  )
  const updateStatus = useUpdateOrderStatus()
  const deleteOrder = useDeleteOrder()

  const filteredOrders = (orders || []).filter(order =>
    searchQuery === '' ||
    order.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    order.user_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleStatusUpdate = async (orderId: string, newStatus: string) => {
    setUpdatingId(orderId)
    try {
      await updateStatus.mutateAsync({ orderId, status: newStatus })
    } finally {
      setUpdatingId(null)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Orders</h1>
          <p className="text-muted-foreground mt-1">Manage and update order statuses</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Filter className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by order ID or user ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {STATUS_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                statusFilter === s
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'border-border hover:bg-muted'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {filteredOrders.length} Order{filteredOrders.length !== 1 ? 's' : ''}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filteredOrders.length === 0 ? (
            <p className="text-center text-muted-foreground py-12">No orders found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Order ID</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">User ID</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Items</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Total</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Date</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order) => (
                    <tr key={order.id} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-3 font-mono text-xs">{order.id.substring(0, 12)}...</td>
                      <td className="py-3 px-3 text-xs text-muted-foreground">{order.user_id.substring(0, 12)}...</td>
                      <td className="py-3 px-3 text-center">{order.items?.length || 0}</td>
                      <td className="py-3 px-3 font-semibold">{formatPrice(order.total_price)}</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[order.status] || 'bg-muted text-muted-foreground'}`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-xs text-muted-foreground">
                        {new Date(order.created_at).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5">
                          {order.status === 'PROCESSING' && (
                            <>
                              <Button
                                size="sm"
                                onClick={() => handleStatusUpdate(order.id, 'CONFIRMED')}
                                disabled={updatingId === order.id}
                                className="h-7 px-2.5 text-xs bg-green-600 hover:bg-green-700 text-white font-medium"
                              >
                                Confirm
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleStatusUpdate(order.id, 'CANCELLED')}
                                disabled={updatingId === order.id}
                                className="h-7 px-2.5 text-xs text-destructive hover:bg-destructive/10 border-destructive/20"
                              >
                                Cancel
                              </Button>
                            </>
                          )}
                          {order.status === 'CONFIRMED' && (
                            <>
                              <Button
                                size="sm"
                                onClick={() => handleStatusUpdate(order.id, 'DELIVERED')}
                                disabled={updatingId === order.id}
                                className="h-7 px-2.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
                              >
                                Deliver
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleStatusUpdate(order.id, 'CANCELLED')}
                                disabled={updatingId === order.id}
                                className="h-7 px-2.5 text-xs text-destructive hover:bg-destructive/10 border-destructive/20"
                              >
                                Cancel
                              </Button>
                            </>
                          )}
                          {(order.status === 'DELIVERED' || order.status === 'CANCELLED') && (
                            <span className="text-muted-foreground text-xs font-normal mr-2">Complete</span>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 h-7 w-7 p-0 shrink-0"
                            onClick={async () => {
                              if (confirm('Are you sure you want to permanently delete this order?')) {
                                setUpdatingId(order.id)
                                try {
                                  await deleteOrder.mutateAsync(order.id)
                                } finally {
                                  setUpdatingId(null)
                                }
                              }
                            }}
                            disabled={updatingId === order.id}
                            title="Delete Order"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
