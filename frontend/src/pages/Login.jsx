import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { DEMO_CREDENTIALS } from '../utils/constants'
import Toast from '../components/Toast'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(username, password)
      setToast({ message: `Welcome, ${user.full_name}`, type: 'success' })
      setTimeout(() => navigate('/dashboard'), 400)
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check credentials.')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (u, p) => {
    setUsername(u)
    setPassword(p)
  }

  return (
    <div className="flex min-h-screen">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <div className="hidden w-1/2 flex-col justify-between bg-navy-950 p-12 text-white lg:flex">
        <div className="flex items-center gap-3">
          <Shield className="h-10 w-10 text-blue-300" />
          <span className="text-2xl font-bold">INSTITRACK</span>
        </div>
        <div>
          <h1 className="text-4xl font-bold leading-tight">
            One Institution.<br />Connected Cases.<br />Smarter Decisions.
          </h1>
          <p className="mt-4 max-w-md text-navy-200">
            Integrated dashboard for monitoring and tracking institution-related complaint cases
            across configurable bureaus and cells. Built for Smart India Hackathon (demonstration).
          </p>
        </div>
        <p className="text-sm text-navy-400">Fictional demonstration data · Not official AICTE records</p>
      </div>

      <div className="flex w-full flex-col justify-center px-6 py-12 lg:w-1/2 lg:px-16">
        <div className="mx-auto w-full max-w-md">
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <Shield className="h-8 w-8 text-navy-900" />
            <span className="text-xl font-bold text-navy-900">INSTITRACK</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900">Sign in</h2>
          <p className="mt-1 text-sm text-slate-500">Access your role-specific dashboard</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}
            <div>
              <label className="label">Username or Email</label>
              <input
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  className="input pr-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                  onClick={() => setShowPw(!showPw)}
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            New complainant?{' '}
            <Link to="/register" className="font-medium text-navy-700 hover:underline">
              Register here
            </Link>
          </p>

          <div className="mt-8 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Demo credentials (SIH)
            </p>
            <div className="space-y-1.5">
              {DEMO_CREDENTIALS.map((d) => (
                <button
                  key={d.username}
                  type="button"
                  onClick={() => fillDemo(d.username, d.password)}
                  className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-xs hover:bg-white"
                >
                  <span className="font-medium text-slate-700">{d.role}</span>
                  <span className="font-mono text-slate-500">{d.username}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
