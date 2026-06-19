import { useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/axios"

export interface OrderResponse {
  id: string
  user_id: string
  total_price: string
  status: string
  items: any[]
}

export interface PaymentResponse {
  id: string
  order_id: string
  status: string
  transaction_id?: string
}

export function useCreateOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      // Order service expects POST /orders/ (it fetches cart_id implicitly based on user JWT)
      const { data } = await apiClient.post<OrderResponse>("/orders/")
      return data
    },
    onSuccess: () => {
      // Invalidate cart since order creation clears it
      queryClient.invalidateQueries({ queryKey: ["cart"] })
    },
  })
}

export function useProcessPayment() {
  return useMutation({
    mutationFn: async ({ order_id, amount, payment_method }: { order_id: string, amount: string | number, payment_method: string }) => {
      // Payment service expects POST /payment/pay/
      const { data } = await apiClient.post<PaymentResponse>("/payment/pay/", {
        order_id,
        amount,
        payment_method,
        simulate_success: true // For demo purposes
      })
      return data
    },
  })
}
