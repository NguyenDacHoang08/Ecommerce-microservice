import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/axios"
import { Cart } from "@/types"
import { useAuthStore } from "@/store/useAuthStore"

export function useCart() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ["cart"],
    queryFn: async () => {
      const { data } = await apiClient.get<Cart>("/cart/")
      return data
    },
    enabled: isAuthenticated, // Only fetch cart if user is logged in
  })
}

export function useAddToCart() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ product_id, quantity }: { product_id: string; quantity: number }) => {
      const { data } = await apiClient.post("/cart/add/", { product_id, quantity })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] })
    },
  })
}

export function useRemoveFromCart() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (item_id: number) => {
      const { data } = await apiClient.delete(`/cart/remove/${item_id}/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] })
    },
  })
}

export function useClearCart() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.delete("/cart/clear/")
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] })
    },
  })
}
