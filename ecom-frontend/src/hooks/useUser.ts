import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/axios"
import { useAuthStore } from "@/store/useAuthStore"

export interface UserProfile {
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
  updated_at: string
  login_count: number
}

export interface UpdateProfilePayload {
  full_name?: string
  phone?: string
  username?: string
}

export function useUserProfile() {
  const { isAuthenticated } = useAuthStore()

  return useQuery({
    queryKey: ["userProfile"],
    queryFn: async () => {
      const { data } = await apiClient.get<UserProfile>("/users/me/")
      return data
    },
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: UpdateProfilePayload) => {
      const { data } = await apiClient.patch<UserProfile>("/users/me/", payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userProfile"] })
    },
  })
}
