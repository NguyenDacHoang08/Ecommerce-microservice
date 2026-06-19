import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface AuthUser {
  id: string
  email: string
  username: string
  full_name: string
  role: 'admin' | 'staff' | 'customer'
  status: string
  email_verified: boolean
  phone?: string
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  user: AuthUser | null
  setTokens: (access: string, refresh: string) => void
  setUser: (user: AuthUser) => void
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      user: null,

      setTokens: (access, refresh) => {
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true })
      },

      setUser: (user) => {
        set({ user })
      },

      logout: async () => {
        const { refreshToken, accessToken } = get()
        if (refreshToken && accessToken) {
          try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:80/api/v1'
            await fetch(`${apiUrl}/auth/logout/`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`,
              },
              body: JSON.stringify({ refresh: refreshToken }),
            })
          } catch {
            // Ignore network errors - still clear local state
          }
        }
        set({ accessToken: null, refreshToken: null, isAuthenticated: false, user: null })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
)
