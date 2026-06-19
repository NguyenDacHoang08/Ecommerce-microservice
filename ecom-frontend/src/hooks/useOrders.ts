import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/axios"
import { useAuthStore } from "@/store/useAuthStore"

export interface OrderItem {
  id: string
  product_id: string
  quantity: number
  price: string
  product_name?: string
}

export interface Order {
  id: string
  user_id: string
  total_price: string
  status: string
  items: OrderItem[]
  created_at: string
  updated_at: string
}

export interface ShipmentStatus {
  id: string
  order_id: string
  status: string
  tracking_number: string
  estimated_delivery: string
  address: string
}

// DRF Pagination wrapper
interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function useOrders() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ["orders"],
    queryFn: async () => {
      const { data } = await apiClient.get<Order[] | PaginatedResponse<Order>>("/orders/")
      // Handle cả trường hợp paginated và non-paginated
      if (Array.isArray(data)) return data
      if (data && typeof data === "object" && "results" in data) return data.results
      return []
    },
    enabled: isAuthenticated,
    staleTime: 1000 * 30, // 30 seconds
  })
}

export function useShipmentStatus(order_id: string) {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ["shipment", order_id],
    queryFn: async () => {
      try {
        const { data } = await apiClient.get<ShipmentStatus>(`/shipping/status/${order_id}/`)
        return data
      } catch {
        return null
      }
    },
    enabled: isAuthenticated && !!order_id,
    staleTime: 1000 * 60,
  })
}
