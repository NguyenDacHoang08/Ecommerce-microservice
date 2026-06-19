import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/axios"

export interface RecommendedProduct {
  product_id: string
  name: string
  score: number
  price?: number
  image_url?: string
  category?: string
  description?: string
  source?: string
  lstm_score?: number
  graph_score?: number
  rag_score?: number
}

export function useRecommendations(userId: string | number | null | undefined, limit = 12) {
  return useQuery({
    queryKey: ["recommendations", userId, limit],
    queryFn: async () => {
      const { data } = await apiClient.get<RecommendedProduct[]>(
        `/recommend/${userId}`,
        { params: { limit } }
      )
      return data
    },
    enabled: !!userId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}
