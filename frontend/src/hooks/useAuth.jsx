import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { login as apiLogin, getMe } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('institack_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('institack_token')
    if (token) {
      getMe()
        .then((res) => {
          setUser(res.data)
          localStorage.setItem('institack_user', JSON.stringify(res.data))
        })
        .catch(() => {
          localStorage.removeItem('institack_token')
          localStorage.removeItem('institack_user')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (username, password) => {
    const res = await apiLogin(username, password)
    const { access_token, user: u } = res.data
    localStorage.setItem('institack_token', access_token)
    localStorage.setItem('institack_user', JSON.stringify(u))
    setUser(u)
    return u
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('institack_token')
    localStorage.removeItem('institack_user')
    setUser(null)
  }, [])

  const hasRole = useCallback(
    (...roles) => (user ? roles.includes(user.role) : false),
    [user]
  )

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasRole, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
