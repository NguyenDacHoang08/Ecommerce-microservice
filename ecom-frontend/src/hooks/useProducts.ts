import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/axios"
import { PaginatedResponse, Product } from "@/types"

interface UseProductsParams {
  page?: number
  search?: string
  category?: string
}

export function useProducts({ page = 1, search = "", category = "" }: UseProductsParams) {
  return useQuery({
    queryKey: ["products", { page, search, category }],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<Product>>("/products/", {
        params: {
          page,
          search: search || undefined,
          category: category || undefined,
        },
      })
      return data
    },
  })
}

export function useProductDetail(id: string) {
  return useQuery({
    queryKey: ["product", id],
    queryFn: async () => {
      const { data } = await apiClient.get<Product>(`/products/${id}/`)
      return data
    },
    enabled: !!id,
  })
}
