import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle } from 'lucide-react'
import { listInstitutionsPublic, submitCase } from '../services/api'
import { CATEGORIES } from '../utils/constants'
import Toast from '../components/Toast'

export default function SubmitComplaint() {
  const navigate = useNavigate()
  const [institutions, setInstitutions] = useState([])
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: CATEGORIES[0],
    institution_id: '',
    incident_date: '',
    contact_phone: '',
    contact_email: '',
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    listInstitutionsPublic({ q: search || undefined })
      .then((r) => setInstitutions(r.data))
      .catch(() => setInstitutions([]))
  }, [search])

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.institution_id) {
      setError('Please select a registered institution')
      return
    }
    if (form.description.length < 20) {
      setError('Description must be at least 20 characters')
      return
    }
    setLoading(true)
    try {
      const payload = {
        ...form,
        institution_id: parseInt(form.institution_id, 10),
        incident_date: form.incident_date ? new Date(form.incident_date).toISOString() : null,
      }
      const res = await submitCase(payload)
      setResult(res.data)
      setToast({ message: `Complaint submitted. Case ID: ${res.data.case_id}`, type: 'success' })
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed. Please try again.')
      setToast({ message: 'Submission failed', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div className="mx-auto max-w-lg">
        {toast && <Toast {...toast} onClose={() => setToast(null)} />}
        <div className="card text-center">
          <CheckCircle className="mx-auto h-16 w-16 text-emerald-500" />
          <h2 className="mt-4 text-2xl font-bold text-slate-900">Complaint Submitted</h2>
          <p className="mt-2 text-slate-600">Your complaint has been registered successfully.</p>
          <div className="mt-6 rounded-lg bg-navy-50 p-4">
            <p className="text-sm text-slate-500">Case ID</p>
            <p className="text-2xl font-bold tracking-wide text-navy-900">{result.case_id}</p>
          </div>
          <p className="mt-4 text-sm text-slate-500">
            Status: <strong>{result.status}</strong>. Authorized officers have been notified.
            You can track progress from your dashboard.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <button className="btn-primary" onClick={() => navigate(`/cases/${result.id}`)}>
              View Case
            </button>
            <button className="btn-secondary" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <h1 className="text-2xl font-bold text-slate-900">Submit Complaint</h1>
      <p className="mt-1 text-sm text-slate-500">
        Select a registered institution and provide details. All fields marked * are required.
      </p>

      <form onSubmit={handleSubmit} className="card mt-6 space-y-5">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        )}

        <div>
          <label className="label">Institution *</label>
          <input
            className="input mb-2"
            placeholder="Search institutions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            name="institution_id"
            className="input"
            value={form.institution_id}
            onChange={handleChange}
            required
          >
            <option value="">Select institution</option>
            {institutions.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name} ({i.institution_id}) — {i.city || i.state}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Category *</label>
          <select name="category" className="input" value={form.category} onChange={handleChange} required>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Title *</label>
          <input
            name="title"
            className="input"
            value={form.title}
            onChange={handleChange}
            required
            minLength={5}
            maxLength={300}
            placeholder="Brief summary of the issue"
          />
        </div>

        <div>
          <label className="label">Detailed Description *</label>
          <textarea
            name="description"
            className="input min-h-[140px]"
            value={form.description}
            onChange={handleChange}
            required
            minLength={20}
            placeholder="Provide a clear, detailed description of the complaint (minimum 20 characters)"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Incident Date (if applicable)</label>
            <input type="date" name="incident_date" className="input" value={form.incident_date} onChange={handleChange} />
          </div>
          <div>
            <label className="label">Contact Phone</label>
            <input name="contact_phone" className="input" value={form.contact_phone} onChange={handleChange} />
          </div>
        </div>

        <div>
          <label className="label">Contact Email</label>
          <input type="email" name="contact_email" className="input" value={form.contact_email} onChange={handleChange} />
        </div>

        <div className="rounded-lg bg-amber-50 px-4 py-3 text-xs text-amber-800">
          Demonstration categories and institutions are fictional and for SIH purposes only.
          Do not submit real personal complaints against actual institutions through this demo.
        </div>

        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? 'Submitting…' : 'Submit Complaint'}
        </button>
      </form>
    </div>
  )
}
