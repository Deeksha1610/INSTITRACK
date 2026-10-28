import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../services/api'
import Toast from '../components/Toast'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', username: '', full_name: '', phone: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register({ ...form, role: 'complainant' })
      setToast({ message: 'Registration successful. Please sign in.', type: 'success' })
      setTimeout(() => navigate('/login'), 1000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <div className="w-full max-w-md card">
        <h1 className="text-2xl font-bold">Register as Complainant</h1>
        <p className="mt-1 text-sm text-slate-500">Create an account to submit and track complaints</p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
          {['full_name', 'username', 'email', 'phone', 'password'].map((field) => (
            <div key={field}>
              <label className="label capitalize">{field.replace('_', ' ')}</label>
              <input
                className="input"
                type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
                value={form[field]}
                onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                required={field !== 'phone'}
                minLength={field === 'password' ? 6 : undefined}
              />
            </div>
          ))}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? 'Registering…' : 'Register'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          Already have an account? <Link to="/login" className="text-navy-700 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
