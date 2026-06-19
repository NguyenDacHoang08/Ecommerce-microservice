import { useState } from 'react'
import { useAdminUsers, useDeleteUser, useActivateUser, useCreateUser, AdminUser } from '@/hooks/useAdmin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Search, RefreshCw, UserCheck, Shield, ShoppingCart, Users, Plus, X, Trash2 } from 'lucide-react'

// ── Simple inline modal ────────────────────────────────────────
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg mx-4 bg-background border rounded-xl shadow-2xl animate-in fade-in-0 zoom-in-95 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b sticky top-0 bg-background">
          <h2 className="font-semibold text-lg">{title}</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-muted transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

// ── Create user form ──────────────────────────────────────────
interface UserFormProps {
  onClose: () => void
}

function UserForm({ onClose }: UserFormProps) {
  const createUser = useCreateUser()
  const [form, setForm] = useState({
    email: '',
    username: '',
    full_name: '',
    phone: '',
    role: 'staff',
    password: '',
  })
  const [error, setError] = useState('')

  const set = (k: string, v: string) => {
    setForm(f => ({ ...f, [k]: v }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!form.email.trim()) { setError('Email is required.'); return }
    if (!form.username.trim()) { setError('Username is required.'); return }
    if (!form.full_name.trim()) { setError('Full Name is required.'); return }
    if (!form.password || form.password.length < 8) { setError('Password must be at least 8 characters long.'); return }

    try {
      await createUser.mutateAsync(form)
      onClose()
    } catch (err: any) {
      const apiError = err?.response?.data
      if (typeof apiError === 'object') {
        const messages = Object.entries(apiError)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('\n')
        setError(messages)
      } else {
        setError(apiError?.detail || 'Something went wrong. Check all fields and try again.')
      }
    }
  }

  const isPending = createUser.isPending

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-4">
        {/* Email */}
        <div className="space-y-1.5">
          <Label htmlFor="uf-email">Email *</Label>
          <Input
            id="uf-email"
            type="email"
            value={form.email}
            onChange={e => set('email', e.target.value)}
            placeholder="e.g. staff@example.com"
            required
          />
        </div>

        {/* Username */}
        <div className="space-y-1.5">
          <Label htmlFor="uf-username">Username *</Label>
          <Input
            id="uf-username"
            value={form.username}
            onChange={e => set('username', e.target.value)}
            placeholder="e.g. staff_member"
            required
          />
        </div>

        {/* Full Name */}
        <div className="space-y-1.5">
          <Label htmlFor="uf-fullname">Full Name *</Label>
          <Input
            id="uf-fullname"
            value={form.full_name}
            onChange={e => set('full_name', e.target.value)}
            placeholder="e.g. John Doe"
            required
          />
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <Label htmlFor="uf-password">Password *</Label>
          <Input
            id="uf-password"
            type="password"
            value={form.password}
            onChange={e => set('password', e.target.value)}
            placeholder="Min 8 characters"
            required
          />
        </div>

        {/* Phone */}
        <div className="space-y-1.5">
          <Label htmlFor="uf-phone">Phone Number</Label>
          <Input
            id="uf-phone"
            value={form.phone}
            onChange={e => set('phone', e.target.value)}
            placeholder="e.g. 0912345678"
          />
        </div>

        {/* Role */}
        <div className="space-y-1.5">
          <Label htmlFor="uf-role">Role *</Label>
          <select
            id="uf-role"
            value={form.role}
            onChange={e => set('role', e.target.value)}
            className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="staff">Staff</option>
            <option value="admin">Admin</option>
            <option value="customer">Customer</option>
          </select>
        </div>
      </div>

      {error && (
        <pre className="text-xs text-destructive bg-destructive/10 px-3 py-2 rounded-md whitespace-pre-wrap border border-destructive/20 font-sans">
          {error}
        </pre>
      )}

      <div className="flex justify-end gap-2 pt-2 border-t">
        <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancel</Button>
        <Button type="submit" size="sm" disabled={isPending}>
          {isPending ? 'Creating…' : 'Create Account'}
        </Button>
      </div>
    </form>
  )
}

// ── Confirm delete user dialog ─────────────────────────────────
function ConfirmDeleteUserDialog({ userEmail, onConfirm, onCancel, isLoading }: {
  userEmail: string; onConfirm: () => void; onCancel: () => void; isLoading: boolean
}) {
  return (
    <Modal title="Confirm Delete User" onClose={onCancel}>
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Are you sure you want to permanently delete the user <span className="font-semibold text-foreground">{userEmail}</span>? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={onConfirm} disabled={isLoading}>
            {isLoading ? 'Deleting…' : 'Delete'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

const ROLE_OPTIONS = ['ALL', 'admin', 'staff', 'customer']

export default function DashboardUsers() {
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('ALL')
  const [actionTarget, setActionTarget] = useState<string | null>(null)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null)

  const { data: users, isLoading, refetch } = useAdminUsers(
    search || undefined,
    roleFilter !== 'ALL' ? roleFilter : undefined
  )
  const deleteUser = useDeleteUser()
  const activateUser = useActivateUser()

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setActionTarget(deleteTarget.id)
    try {
      await deleteUser.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
    } finally {
      setActionTarget(null)
    }
  }

  const handleActivate = async (userId: string) => {
    setActionTarget(userId)
    try {
      await activateUser.mutateAsync(userId)
    } finally {
      setActionTarget(null)
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <Shield className="h-3 w-3" />
      case 'staff': return <Users className="h-3 w-3" />
      default: return <ShoppingCart className="h-3 w-3" />
    }
  }

  const getRoleBadgeVariant = (role: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (role) {
      case 'admin': return 'default'
      case 'staff': return 'secondary'
      default: return 'outline'
    }
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground mt-1">Manage user accounts and permissions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </Button>
          <Button size="sm" onClick={() => setIsCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Add Staff Account
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, email, username..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          {ROLE_OPTIONS.map((r) => (
            <button
              key={r}
              onClick={() => setRoleFilter(r)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border capitalize transition-all ${
                roleFilter === r
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'border-border hover:bg-muted'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {(users || []).length} User{(users || []).length !== 1 ? 's' : ''}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : !users || users.length === 0 ? (
            <p className="text-center text-muted-foreground py-12">No users found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">User</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Role</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Email Verified</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Logins</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Joined</th>
                    <th className="text-left py-3 px-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                            <span className="text-xs font-bold text-primary">
                              {(user.full_name || user.email)[0].toUpperCase()}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium">{user.full_name || '—'}</p>
                            <p className="text-xs text-muted-foreground">{user.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant={getRoleBadgeVariant(user.role)} className="gap-1 capitalize">
                          {getRoleIcon(user.role)} {user.role}
                        </Badge>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${
                          user.is_active
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                            : 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                        }`}>
                          {!user.is_active ? 'inactive' : user.status}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={user.email_verified ? 'text-green-600' : 'text-muted-foreground'}>
                          {user.email_verified ? '✓ Verified' : '✗ Unverified'}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">{user.login_count ?? '—'}</td>
                      <td className="py-3 px-3 text-xs text-muted-foreground">
                        {new Date(user.created_at).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="py-3 px-3">
                        {user.role !== 'admin' && (
                          user.is_active ? (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-destructive hover:bg-destructive/10 hover:text-destructive h-8"
                              onClick={() => setDeleteTarget(user)}
                              disabled={actionTarget === user.id}
                            >
                              <Trash2 className="mr-1 h-3.5 w-3.5" /> Delete
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-green-600 hover:bg-green-100 hover:text-green-700 h-8"
                              onClick={() => handleActivate(user.id)}
                              disabled={actionTarget === user.id}
                            >
                              <UserCheck className="mr-1 h-3.5 w-3.5" /> Activate
                            </Button>
                          )
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {isCreateOpen && (
        <Modal title="Create Staff / User Account" onClose={() => setIsCreateOpen(false)}>
          <UserForm onClose={() => setIsCreateOpen(false)} />
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDeleteUserDialog
          userEmail={deleteTarget.email}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeleteTarget(null)}
          isLoading={actionTarget === deleteTarget.id}
        />
      )}
    </div>
  )
}
