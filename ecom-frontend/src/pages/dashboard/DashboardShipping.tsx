import { useState } from 'react'
import { useAdminShipments, useUpdateShipment, useDeleteShipment } from '@/hooks/useAdmin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { RefreshCw, Truck, Filter, ChevronDown, Package, Trash2 } from 'lucide-react'

const STATUS_OPTIONS = ['ALL', 'PROCESSING', 'SHIPPING', 'DELIVERED']

const statusColors: Record<string, string> = {
  PROCESSING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
  SHIPPING:   'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  DELIVERED:  'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
}

export default function DashboardShipping() {
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const { data: shipments, isLoading, refetch } = useAdminShipments(
    statusFilter !== 'ALL' ? statusFilter : undefined
  )
  const updateShipment = useUpdateShipment()
  const deleteShipment = useDeleteShipment()

  const filtered = (shipments || []).filter(s => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      s.id.toLowerCase().includes(q) ||
      s.order_id.toLowerCase().includes(q) ||
      (s.tracking_number || '').toLowerCase().includes(q)
    )
  })

  const handleStatusUpdate = async (id: string, status: string) => {
    setUpdatingId(id)
    try {
      await updateShipment.mutateAsync({ id, payload: { status } })
    } finally {
      setUpdatingId(null)
    }
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Shipping</h1>
          <p className="text-muted-foreground mt-1">Track and manage shipments</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        {['PROCESSING', 'SHIPPING', 'DELIVERED'].map(s => {
          const count = (shipments || []).filter(x => x.status === s).length
          return (
            <button
              key={s}
              onClick={() => setStatusFilter(statusFilter === s ? 'ALL' : s)}
              className={`rounded-lg border p-3 text-left transition-all hover:shadow-sm ${
                statusFilter === s ? 'border-primary bg-primary/5' : 'bg-card hover:bg-muted/50'
              }`}
            >
              <p className="text-2xl font-bold">{count}</p>
              <p className="text-xs text-muted-foreground capitalize mt-0.5">{s.toLowerCase()}</p>
            </button>
          )
        })}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Filter className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by order ID or tracking number…"
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
            {filtered.length} Shipment{filtered.length !== 1 ? 's' : ''}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16">
              <Package className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No shipments found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Shipment ID</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Order ID</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Tracking #</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Carrier</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Est. Delivery</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((s) => (
                    <tr key={s.id} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-3 font-mono text-xs">{s.id.substring(0, 10)}…</td>
                      <td className="py-3 px-3 font-mono text-xs text-muted-foreground">{s.order_id.substring(0, 10)}…</td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5">
                          <Truck className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                          <span className="font-mono text-xs">{s.tracking_number || '—'}</span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-sm">{s.carrier || '—'}</td>
                      <td className="py-3 px-3 text-xs text-muted-foreground">
                        {s.estimated_delivery
                          ? new Date(s.estimated_delivery).toLocaleDateString('vi-VN')
                          : '—'}
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[s.status] || 'bg-muted text-muted-foreground'}`}>
                          {s.status}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <div className="relative inline-block">
                            <select
                              value={s.status}
                              onChange={(e) => handleStatusUpdate(s.id, e.target.value)}
                              disabled={updatingId === s.id}
                              className="appearance-none text-xs border rounded-md px-2 py-1.5 pr-6 bg-background hover:bg-muted transition-colors cursor-pointer disabled:opacity-50"
                            >
                              {STATUS_OPTIONS.filter(x => x !== 'ALL').map(x => (
                                <option key={x} value={x}>{x}</option>
                              ))}
                            </select>
                            <ChevronDown className="absolute right-1.5 top-2 h-3 w-3 text-muted-foreground pointer-events-none" />
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 h-7 w-7 p-0 shrink-0"
                            onClick={async () => {
                              if (confirm('Are you sure you want to permanently delete this shipment?')) {
                                setUpdatingId(s.id)
                                try {
                                  await deleteShipment.mutateAsync(s.id)
                                } finally {
                                  setUpdatingId(null)
                                }
                              }
                            }}
                            disabled={updatingId === s.id}
                            title="Delete Shipment"
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
