import { useEffect, useState } from 'react'
import { listCoordination, createCoordination, respondCoordination, listCases, listBureaus } from '../services/api'
import Loading, { EmptyState } from '../components/Loading'
import Toast from '../components/Toast'
import { useAuth } from '../hooks/useAuth'

export default function Coordination() {
  const { hasRole } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [cases, setCases] = useState([])
  const [bureaus, setBureaus] = useState([])
  const [form, setForm] = useState({ case_id: '', to_bureau_id: '', reason: '', requested_action: '' })
  const [respondId, setRespondId] = useState(null)
  const [response, setResponse] = useState('')

  const load = () => {
    listCoordination().then((r) => setItems(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openCreate = async () => {
    const [c, b] = await Promise.all([listCases({ page_size: 50 }), listBureaus()])
    setCases(c.data.items || [])
    setBureaus(b.data)
    setShowCreate(true)
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await createCoordination({
        case_id: parseInt(form.case_id, 10),
        to_bureau_id: parseInt(form.to_bureau_id, 10),
        reason: form.reason,
        requested_action: form.requested_action || null,
      })
      setToast({ message: 'Coordination request created', type: 'success' })
      setShowCreate(false)
      load()
    } catch (err) {
      setToast({ message: err.response?.data?.detail || 'Failed', type: 'error' })
    }
  }

  const handleRespond = async () => {
    try {
      await respondCoordination(respondId, { response, mark_completed: true })
      setToast({ message: 'Response submitted', type: 'success' })
      setRespondId(null)
      load()
    } catch (err) {
      setToast({ message: err.response?.data?.detail || 'Failed', type: 'error' })
    }
  }

  if (loading) return <Loading />

  return (
    <div className="space-y-4">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Coordination Centre</h1>
        {hasRole('bureau_officer', 'central_monitoring', 'super_admin') && (
          <button className="btn-primary" onClick={openCreate}>New Request</button>
        )}
      </div>
      {items.length === 0 ? (
        <EmptyState title="No coordination requests" description="Initiate cross-bureau coordination from here or case detail." />
      ) : (
        <div className="space-y-3">
          {items.map((cr) => (
            <div key={cr.id} className="card">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium">Case {cr.case_public_id}</p>
                  <p className="text-sm text-slate-600">{cr.from_bureau_name} → {cr.to_bureau_name}</p>
                  <p className="mt-1 text-sm">{cr.reason}</p>
                  {cr.response && <p className="mt-2 rounded bg-slate-50 p-2 text-sm"><strong>Response:</strong> {cr.response}</p>}
                </div>
                <span className={`badge ${cr.status === 'PENDING' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
                  {cr.status}
                </span>
              </div>
              {cr.status === 'PENDING' && hasRole('bureau_officer', 'super_admin') && (
                <button className="btn-secondary mt-3 text-sm" onClick={() => setRespondId(cr.id)}>Respond</button>
              )}
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setShowCreate(false)}>
          <form className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl space-y-3" onClick={(e) => e.stopPropagation()} onSubmit={handleCreate}>
            <h3 className="text-lg font-semibold">New Coordination Request</h3>
            <select className="input" required value={form.case_id} onChange={(e) => setForm((f) => ({ ...f, case_id: e.target.value }))}>
              <option value="">Select case</option>
              {cases.map((c) => <option key={c.id} value={c.id}>{c.case_id} — {c.title.slice(0, 40)}</option>)}
            </select>
            <select className="input" required value={form.to_bureau_id} onChange={(e) => setForm((f) => ({ ...f, to_bureau_id: e.target.value }))}>
              <option value="">Target bureau</option>
              {bureaus.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
            <textarea className="input" required minLength={5} placeholder="Reason" value={form.reason} onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))} />
            <textarea className="input" placeholder="Requested action (optional)" value={form.requested_action} onChange={(e) => setForm((f) => ({ ...f, requested_action: e.target.value }))} />
            <button type="submit" className="btn-primary w-full">Create</button>
          </form>
        </div>
      )}

      {respondId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setRespondId(null)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl space-y-3" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold">Respond to Request</h3>
            <textarea className="input min-h-[100px]" value={response} onChange={(e) => setResponse(e.target.value)} placeholder="Your response..." />
            <button className="btn-primary w-full" disabled={response.length < 5} onClick={handleRespond}>Submit Response</button>
          </div>
        </div>
      )}
    </div>
  )
}
