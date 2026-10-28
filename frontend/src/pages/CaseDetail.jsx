import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getCase, acceptCase, rejectCase, requestInfo, assignCase, acknowledgeAssignment,
  updateStatus, submitResolution, approveClosure, getRelated, respondInfo,
  listBureaus, listOfficers, recommendBureau, addComment
} from '../services/api'
import { useAuth } from '../hooks/useAuth'
import { StatusBadge, PriorityBadge } from '../components/StatusBadge'
import Loading from '../components/Loading'
import Toast from '../components/Toast'

export default function CaseDetail() {
  const { id } = useParams()
  const { user, hasRole } = useAuth()
  const navigate = useNavigate()
  const [caseData, setCaseData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  // Modals / forms
  const [showReject, setShowReject] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [showInfoReq, setShowInfoReq] = useState(false)
  const [infoText, setInfoText] = useState('')
  const [showAssign, setShowAssign] = useState(false)
  const [bureaus, setBureaus] = useState([])
  const [officers, setOfficers] = useState([])
  const [assignForm, setAssignForm] = useState({ bureau_id: '', officer_id: '', priority: 'MEDIUM', notes: '', deadline: '' })
  const [showResolution, setShowResolution] = useState(false)
  const [resolutionText, setResolutionText] = useState('')
  const [showRespond, setShowRespond] = useState(false)
  const [respondText, setRespondText] = useState('')
  const [related, setRelated] = useState([])
  const [comment, setComment] = useState('')

  const load = () => {
    setLoading(true)
    getCase(id)
      .then((r) => setCaseData(r.data))
      .catch((e) => {
        if (e.response?.status === 403 || e.response?.status === 404) navigate('/cases')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  const act = async (fn, successMsg) => {
    setActionLoading(true)
    try {
      await fn()
      setToast({ message: successMsg, type: 'success' })
      load()
    } catch (e) {
      setToast({ message: e.response?.data?.detail || 'Action failed', type: 'error' })
    } finally {
      setActionLoading(false)
    }
  }

  const openAssign = async () => {
    const [b, rec] = await Promise.all([
      listBureaus(),
      caseData ? recommendBureau(caseData.category).catch(() => ({ data: {} })) : Promise.resolve({ data: {} }),
    ])
    setBureaus(b.data)
    const bureauId = rec.data?.recommended_bureau_id || ''
    setAssignForm((f) => ({ ...f, bureau_id: bureauId ? String(bureauId) : '' }))
    if (bureauId) {
      const o = await listOfficers(bureauId)
      setOfficers(o.data)
    }
    setShowAssign(true)
  }

  const onBureauChange = async (bureauId) => {
    setAssignForm((f) => ({ ...f, bureau_id: bureauId, officer_id: '' }))
    if (bureauId) {
      const o = await listOfficers(bureauId)
      setOfficers(o.data)
    } else setOfficers([])
  }

  const loadRelated = async () => {
    try {
      const r = await getRelated(id)
      setRelated(r.data)
    } catch {}
  }

  if (loading || !caseData) return <Loading />

  const c = caseData
  const isMonitor = hasRole('central_monitoring', 'super_admin')
  const isOfficer = hasRole('bureau_officer', 'super_admin')
  const isComplainant = hasRole('complainant')
  const isAuditor = hasRole('auditor')

  return (
    <div className="space-y-6">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">{c.case_id}</h1>
            <StatusBadge status={c.status} />
            <PriorityBadge priority={c.priority} />
            {c.is_overdue && <span className="badge bg-red-100 text-red-700">OVERDUE</span>}
          </div>
          <p className="mt-1 text-lg text-slate-700">{c.title}</p>
          <p className="text-sm text-slate-500">
            {c.institution?.name} · {c.category} · Submitted {new Date(c.created_at).toLocaleString()}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          {isMonitor && ['SUBMITTED', 'UNDER_REVIEW', 'NEEDS_INFORMATION'].includes(c.status) && (
            <>
              <button className="btn-success" disabled={actionLoading} onClick={() => act(() => acceptCase(id), 'Case accepted')}>
                Accept
              </button>
              <button className="btn-warning" onClick={() => setShowInfoReq(true)}>Request Info</button>
              <button className="btn-danger" onClick={() => setShowReject(true)}>Reject</button>
            </>
          )}
          {isMonitor && ['ACCEPTED', 'RETURNED', 'REOPENED', 'ESCALATED'].includes(c.status) && (
            <button className="btn-primary" onClick={openAssign}>Assign</button>
          )}
          {isOfficer && c.status === 'ASSIGNED' && (
            <button className="btn-primary" disabled={actionLoading} onClick={() => act(() => acknowledgeAssignment(id), 'Assignment acknowledged')}>
              Acknowledge Assignment
            </button>
          )}
          {isOfficer && ['IN_PROGRESS', 'ASSIGNED', 'ESCALATED'].includes(c.status) && (
            <button className="btn-success" onClick={() => setShowResolution(true)}>Submit Resolution</button>
          )}
          {isMonitor && c.status === 'RESOLUTION_SUBMITTED' && (
            <>
              <button className="btn-success" disabled={actionLoading} onClick={() => act(() => approveClosure(id, { approve: true, remarks: 'Approved' }), 'Case closed')}>
                Approve Closure
              </button>
              <button className="btn-warning" disabled={actionLoading} onClick={() => act(() => approveClosure(id, { approve: false, remarks: 'Returned for rework' }), 'Returned for rework')}>
                Return for Rework
              </button>
            </>
          )}
          {isComplainant && c.status === 'NEEDS_INFORMATION' && (
            <button className="btn-primary" onClick={() => setShowRespond(true)}>Provide Information</button>
          )}
          {isMonitor && (
            <button className="btn-secondary" onClick={loadRelated}>Find Related Cases</button>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="space-y-6 lg:col-span-2">
          <div className="card">
            <h2 className="mb-3 font-semibold">Description</h2>
            <p className="whitespace-pre-wrap text-sm text-slate-700">{c.description}</p>
          </div>

          {c.information_request && (
            <div className="card border-orange-200 bg-orange-50">
              <h2 className="mb-2 font-semibold text-orange-800">Information Requested</h2>
              <p className="text-sm text-orange-900">{c.information_request}</p>
              {c.complainant_response && (
                <div className="mt-3 border-t border-orange-200 pt-3">
                  <p className="text-xs font-medium text-orange-700">Complainant Response:</p>
                  <p className="text-sm">{c.complainant_response}</p>
                </div>
              )}
            </div>
          )}

          {c.resolution_summary && (
            <div className="card border-teal-200 bg-teal-50">
              <h2 className="mb-2 font-semibold text-teal-800">Resolution Summary</h2>
              <p className="text-sm text-teal-900">{c.resolution_summary}</p>
            </div>
          )}

          {c.rejection_reason && (
            <div className="card border-red-200 bg-red-50">
              <h2 className="mb-2 font-semibold text-red-800">Rejection Reason</h2>
              <p className="text-sm text-red-900">{c.rejection_reason}</p>
            </div>
          )}

          {/* Timeline */}
          <div className="card">
            <h2 className="mb-4 font-semibold">Case Timeline</h2>
            <ol className="relative border-l border-slate-200 pl-6">
              {(c.history || []).map((h) => (
                <li key={h.id} className="mb-4">
                  <div className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full border-2 border-white bg-navy-500" />
                  <p className="text-sm font-medium">{h.action.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-slate-500">
                    {h.actor?.full_name || 'System'} · {new Date(h.created_at).toLocaleString()}
                    {h.from_status && h.to_status && ` · ${h.from_status} → ${h.to_status}`}
                  </p>
                  {h.remarks && <p className="mt-1 text-sm text-slate-600">{h.remarks}</p>}
                </li>
              ))}
            </ol>
          </div>

          {/* Comments */}
          {!isAuditor && (
            <div className="card">
              <h2 className="mb-3 font-semibold">Add Remark / Comment</h2>
              <textarea className="input min-h-[80px]" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Progress remark..." />
              <button
                className="btn-secondary mt-2"
                disabled={!comment.trim() || actionLoading}
                onClick={() => act(async () => {
                  await addComment(id, comment, !isComplainant)
                  setComment('')
                }, 'Comment added')}
              >
                Add Comment
              </button>
              {(c.comments || []).length > 0 && (
                <ul className="mt-4 space-y-2 border-t pt-4">
                  {c.comments.map((cm) => (
                    <li key={cm.id} className="text-sm">
                      <span className="font-medium">{cm.author?.full_name}</span>
                      <span className="text-xs text-slate-400"> · {new Date(cm.created_at).toLocaleString()}</span>
                      {cm.is_internal && <span className="ml-1 badge bg-slate-100 text-slate-600">Internal</span>}
                      <p className="text-slate-700">{cm.content}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="card space-y-3 text-sm">
            <h2 className="font-semibold">Details</h2>
            <Row label="Institution" value={c.institution?.name} />
            <Row label="Institution ID" value={c.institution?.institution_id} />
            <Row label="Assigned Bureau" value={c.assigned_bureau_name || '—'} />
            <Row label="Assigned Officer" value={c.assigned_officer?.full_name || '—'} />
            <Row label="Deadline" value={c.deadline ? new Date(c.deadline).toLocaleDateString() : '—'} />
            <Row label="Version" value={c.version} />
          </div>

          {(c.assignments || []).length > 0 && (
            <div className="card">
              <h2 className="mb-3 font-semibold">Assignment History</h2>
              {c.assignments.map((a) => (
                <div key={a.id} className="mb-3 border-b pb-2 text-sm last:border-0">
                  <p className="font-medium">{a.bureau_name} {a.is_current && <span className="badge bg-emerald-100 text-emerald-700">Current</span>}</p>
                  <p className="text-xs text-slate-500">
                    Officer: {a.officer_name || 'Unassigned'} · {a.acknowledged ? 'Acknowledged' : 'Pending ack'}
                  </p>
                  {a.notes && <p className="text-xs text-slate-600">{a.notes}</p>}
                </div>
              ))}
            </div>
          )}

          {related.length > 0 && (
            <div className="card">
              <h2 className="mb-3 font-semibold">AI Related Cases</h2>
              <p className="mb-2 text-xs text-slate-500">Suggestions based on TF-IDF similarity — not proof of duplication.</p>
              {related.map((r) => (
                <div key={r.target_case_id} className="mb-2 rounded border p-2 text-sm">
                  <button className="font-medium text-navy-700 hover:underline" onClick={() => navigate(`/cases/${r.target_case_id}`)}>
                    {r.target_case_public_id}
                  </button>
                  <p className="text-xs text-slate-500">Score: {(r.similarity_score * 100).toFixed(1)}%</p>
                  <p className="truncate text-xs">{r.target_title}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showReject && (
        <Modal title="Reject Case" onClose={() => setShowReject(false)}>
          <textarea className="input min-h-[100px]" placeholder="Reason for rejection (required)" value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} />
          <button
            className="btn-danger mt-3 w-full"
            disabled={rejectReason.length < 5 || actionLoading}
            onClick={() => act(async () => { await rejectCase(id, { reason: rejectReason }); setShowReject(false) }, 'Case rejected')}
          >
            Confirm Reject
          </button>
        </Modal>
      )}

      {showInfoReq && (
        <Modal title="Request Additional Information" onClose={() => setShowInfoReq(false)}>
          <textarea className="input min-h-[100px]" placeholder="What information is needed?" value={infoText} onChange={(e) => setInfoText(e.target.value)} />
          <button
            className="btn-warning mt-3 w-full"
            disabled={infoText.length < 5 || actionLoading}
            onClick={() => act(async () => { await requestInfo(id, { information_request: infoText }); setShowInfoReq(false) }, 'Information requested')}
          >
            Send Request
          </button>
        </Modal>
      )}

      {showRespond && (
        <Modal title="Provide Additional Information" onClose={() => setShowRespond(false)}>
          <textarea className="input min-h-[100px]" placeholder="Your response..." value={respondText} onChange={(e) => setRespondText(e.target.value)} />
          <button
            className="btn-primary mt-3 w-full"
            disabled={respondText.length < 5 || actionLoading}
            onClick={() => act(async () => { await respondInfo(id, { response: respondText }); setShowRespond(false) }, 'Response submitted')}
          >
            Submit Response
          </button>
        </Modal>
      )}

      {showAssign && (
        <Modal title="Assign Case" onClose={() => setShowAssign(false)}>
          <div className="space-y-3">
            <div>
              <label className="label">Bureau / Cell *</label>
              <select className="input" value={assignForm.bureau_id} onChange={(e) => onBureauChange(e.target.value)}>
                <option value="">Select bureau</option>
                {bureaus.map((b) => <option key={b.id} value={b.id}>{b.name} ({b.code})</option>)}
              </select>
            </div>
            <div>
              <label className="label">Officer</label>
              <select className="input" value={assignForm.officer_id} onChange={(e) => setAssignForm((f) => ({ ...f, officer_id: e.target.value }))}>
                <option value="">Any / Unassigned</option>
                {officers.map((o) => <option key={o.id} value={o.id}>{o.full_name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Priority</label>
              <select className="input" value={assignForm.priority} onChange={(e) => setAssignForm((f) => ({ ...f, priority: e.target.value }))}>
                {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Notes</label>
              <textarea className="input" value={assignForm.notes} onChange={(e) => setAssignForm((f) => ({ ...f, notes: e.target.value }))} />
            </div>
            <button
              className="btn-primary w-full"
              disabled={!assignForm.bureau_id || actionLoading}
              onClick={() => act(async () => {
                await assignCase(id, {
                  bureau_id: parseInt(assignForm.bureau_id, 10),
                  officer_id: assignForm.officer_id ? parseInt(assignForm.officer_id, 10) : null,
                  priority: assignForm.priority,
                  notes: assignForm.notes || null,
                })
                setShowAssign(false)
              }, 'Case assigned')}
            >
              Assign
            </button>
          </div>
        </Modal>
      )}

      {showResolution && (
        <Modal title="Submit Resolution" onClose={() => setShowResolution(false)}>
          <textarea className="input min-h-[120px]" placeholder="Resolution summary (required)" value={resolutionText} onChange={(e) => setResolutionText(e.target.value)} />
          <button
            className="btn-success mt-3 w-full"
            disabled={resolutionText.length < 10 || actionLoading}
            onClick={() => act(async () => { await submitResolution(id, { resolution_summary: resolutionText }); setShowResolution(false) }, 'Resolution submitted')}
          >
            Submit Resolution
          </button>
        </Modal>
      )}
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-medium text-slate-800">{value}</span>
    </div>
  )
}

function Modal({ title, children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h3 className="mb-4 text-lg font-semibold">{title}</h3>
        {children}
      </div>
    </div>
  )
}
