import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/axios"

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AdminUser {
  id: string
  email: string
  username: string
  full_name: string
  phone: string | null
  role: string
  status: string
  is_active: boolean
  email_verified: boolean
  created_at: string
  login_count: number
}

export interface AdminOrder {
  id: string
  user_id: string
  total_price: string
  status: string
  created_at: string
  items: { id: string; product_id: string; quantity: number; price: string }[]
}

export interface AdminProduct {
  id: string
  sku: string
  name: string
  slug?: string
  description?: string
  price: string
  sale_price?: string
  quantity: number
  stock_status: string
  status: string           // 'draft' | 'active' | 'inactive' | 'deleted'
  category?: { id: string; name: string; slug: string }
  category_name?: string
  created_at?: string
  images?: { id?: string; url: string; alt_text?: string; is_primary?: boolean; order?: number }[]
}

export interface AdminCategory {
  id: string
  name: string
  slug: string
  parent?: string | null
  is_active: boolean
}

export interface ProductPayload {
  name: string
  description?: string
  price: string
  quantity: number
  status: 'draft' | 'active' | 'inactive'
  category: string          // category UUID
  currency?: string
  sku?: string
  images?: { url: string; alt_text?: string; is_primary?: boolean }[]
}

export interface AdminShipment {
  id: string
  order_id: string
  tracking_number: string
  carrier: string
  status: string
  estimated_delivery: string
  created_at: string
  updated_at: string
}

// ── Users ─────────────────────────────────────────────────────
export interface CreateUserPayload {
  email: string
  username: string
  full_name: string
  phone?: string
  role: string
  password?: string
  is_staff?: boolean
  status?: string
}

export function useAdminUsers(search?: string, role?: string) {
  return useQuery({
    queryKey: ["admin", "users", search, role],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (search) params.set("search", search)
      if (role) params.set("role", role)
      const { data } = await apiClient.get<AdminUser[] | PaginatedResponse<AdminUser>>(
        `/users/?${params.toString()}`
      )
      if (Array.isArray(data)) return data
      if (data && "results" in data) return data.results
      return []
    },
    staleTime: 1000 * 30,
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateUserPayload) => {
      const { data } = await apiClient.post<AdminUser>(`/users/`, payload)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  })
}

export function useDeleteUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) => {
      const { data } = await apiClient.delete(`/users/${userId}/`)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  })
}

export function useActivateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) => {
      const { data } = await apiClient.post(`/users/${userId}/activate/`)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  })
}

// ── All Orders (Admin) ─────────────────────────────────────────
export function useAdminOrders(status?: string) {
  return useQuery({
    queryKey: ["admin", "orders", status],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (status) params.set("status", status)
      const { data } = await apiClient.get<AdminOrder[] | PaginatedResponse<AdminOrder>>(
        `/orders/?${params.toString()}`
      )
      if (Array.isArray(data)) return data
      if (data && "results" in data) return data.results
      return []
    },
    staleTime: 1000 * 30,
  })
}

export function useUpdateOrderStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ orderId, status }: { orderId: string; status: string }) => {
      const { data } = await apiClient.patch(`/orders/${orderId}/`, { status })
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "orders"] }),
  })
}

// ── Products (Admin CRUD) ──────────────────────────────────────
export function useAdminProducts(search?: string) {
  return useQuery({
    queryKey: ["admin", "products", search],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (search) params.set("search", search)
      // Staff can see all statuses
      const { data } = await apiClient.get<AdminProduct[] | PaginatedResponse<AdminProduct>>(
        `/products/?${params.toString()}`
      )
      if (Array.isArray(data)) return data
      if (data && "results" in data) return data.results
      return []
    },
    staleTime: 1000 * 30,
  })
}

export function useAdminCategories() {
  return useQuery({
    queryKey: ["admin", "categories"],
    queryFn: async () => {
      // Fetch ALL categories (root + children) by querying without parent filter
      // Use search trick: fetch root categories
      const allCats: AdminCategory[] = []

      // Fetch root categories
      const rootRes = await apiClient.get<AdminCategory[] | PaginatedResponse<AdminCategory>>(`/categories/`)
      const roots = Array.isArray(rootRes.data) ? rootRes.data
        : (rootRes.data && 'results' in rootRes.data ? rootRes.data.results : [])
      allCats.push(...roots)

      // Fetch subcategories for each root
      for (const root of roots) {
        try {
          const childRes = await apiClient.get<AdminCategory[] | PaginatedResponse<AdminCategory>>(
            `/categories/?parent=${root.id}`
          )
          const children = Array.isArray(childRes.data) ? childRes.data
            : (childRes.data && 'results' in childRes.data ? childRes.data.results : [])
          allCats.push(...children)
        } catch {
          // ignore
        }
      }

      return allCats
    },
    staleTime: 1000 * 60 * 5,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: ProductPayload) => {
      const { data } = await apiClient.post<AdminProduct>(`/products/`, payload)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "products"] }),
  })
}

export function useUpdateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<ProductPayload> }) => {
      const { data } = await apiClient.patch<AdminProduct>(`/products/${id}/`, payload)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "products"] }),
  })
}

export function useDeleteProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/products/${id}/`)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "products"] }),
  })
}

// ── Shipping (Admin) ───────────────────────────────────────────
export function useAdminShipments(status?: string) {
  return useQuery({
    queryKey: ["admin", "shipments", status],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (status) params.set("status", status)
      const { data } = await apiClient.get<AdminShipment[] | PaginatedResponse<AdminShipment>>(
        `/shipping/?${params.toString()}`
      )
      if (Array.isArray(data)) return data
      if (data && "results" in data) return data.results
      return []
    },
    staleTime: 1000 * 30,
  })
}

export function useUpdateShipment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: { status?: string; tracking_number?: string; carrier?: string; estimated_delivery?: string } }) => {
      const { data } = await apiClient.patch<AdminShipment>(`/shipping/${id}/`, payload)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "shipments"] }),
  })
}

export function useDeleteShipment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/shipping/${id}/`)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "shipments"] }),
  })
}

export function useDeleteOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/orders/${id}/`)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "orders"] }),
  })
}
