import { useState } from 'react'
import { Download } from 'lucide-react'
import { exportCasesCsv, exportCasesPdf, getAuditLogs } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import Toast from '../components/Toast'

export default function Reports() {
  const { hasRole } = useAuth()
  const [toast, setToast] = useState(null)
  const [auditLogs, setAuditLogs] = useState([])

  const download = async (fn, filename) => {
    try {
      const res = await fn()
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      window.URL.revokeObjectURL(url)
      setToast({ message: 'Download started', type: 'success' })
    } catch {
      setToast({ message: 'Export failed', type: 'error' })
    }
  }

  const loadAudit = async () => {
    const r = await getAuditLogs()
    setAuditLogs(r.data)
  }

  return (
    <div className="space-y-6">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      <h1 className="text-2xl font-bold">Reports & Exports</h1>
      <p className="text-sm text-slate-500">Exports contain authorized database records only. Demonstration data.</p>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="card">
          <h2 className="font-semibold">Case Export (CSV)</h2>
          <p className="mt-1 text-sm text-slate-500">Download cases as CSV for analysis.</p>
          <button className="btn-primary mt-4" onClick={() => download(exportCasesCsv, 'institack_cases.csv')}>
            <Download className="h-4 w-4" /> Download CSV
          </button>
        </div>
        <div className="card">
          <h2 className="font-semibold">Case Report (PDF)</h2>
          <p className="mt-1 text-sm text-slate-500">Generate a PDF summary report.</p>
          <button className="btn-primary mt-4" onClick={() => download(exportCasesPdf, 'institack_cases.pdf')}>
            <Download className="h-4 w-4" /> Download PDF
          </button>
        </div>
      </div>

      {hasRole('auditor', 'super_admin', 'central_monitoring') && (
        <div className="card">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Audit Logs</h2>
            <button className="btn-secondary text-sm" onClick={loadAudit}>Load Audit Logs</button>
          </div>
          {auditLogs.length > 0 && (
            <div className="mt-4 max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="border-b text-xs uppercase text-slate-500">
                  <tr>
                    <th className="py-2 text-left">Action</th>
                    <th className="py-2 text-left">Entity</th>
                    <th className="py-2 text-left">User</th>
                    <th className="py-2 text-left">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((l) => (
                    <tr key={l.id} className="border-b">
                      <td className="py-2">{l.action}</td>
                      <td className="py-2">{l.entity_type} {l.entity_id}</td>
                      <td className="py-2">{l.user?.full_name || '—'}</td>
                      <td className="py-2 text-slate-500">{new Date(l.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
