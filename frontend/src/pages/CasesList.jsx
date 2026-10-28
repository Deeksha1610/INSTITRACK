import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Search, Filter } from 'lucide-react'
import { listCases } from '../services/api'
import { StatusBadge, PriorityBadge } from '../components/StatusBadge'
import Loading, { EmptyState } from '../components/Loading'
import { CATEGORIES } from '../utils/constants'

const STATUSES = [
  'SUBMITTED', 'UNDER_REVIEW', 'ACCEPTED', 'ASSIGNED', 'IN_PROGRESS',
  'NEEDS_INFORMATION', 'RETURNED', 'REJECTED', 'RESOLUTION_SUBMITTED',
  'ESCALATED', 'CLOSED', 'REOPENED',
]

export default function CasesList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState(searchParams.get('q') || '')
  const status = searchParams.get('status') || ''
  const category = searchParams.get('category') || ''
  const overdue = searchParams.get('overdue') || ''
  const page = parseInt(searchParams.get('page') || '1', 10)

  useEffect(() => {
    setLoading(true)
    const params = { page, page_size: 15 }
    if (status) params.status = status
    if (category) params.category = category
    if (overdue) params.overdue = overdue === 'true'
    if (q) params.q = q
    listCases(params)
      .then((r) => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [status, category, overdue, page, searchParams])

  const updateFilter = (key, value) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.delete('page')
    setSearchParams(next)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    updateFilter('q', q)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-900">Cases</h1>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              className="input pl-9 w-56"
              placeholder="Search Case ID or title..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-secondary">Search</button>
        </form>
      </div>

      <div className="flex flex-wrap gap-2">
        <select className="input w-auto" value={status} onChange={(e) => updateFilter('status', e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
        </select>
        <select className="input w-auto" value={category} onChange={(e) => updateFilter('category', e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select className="input w-auto" value={overdue} onChange={(e) => updateFilter('overdue', e.target.value)}>
          <option value="">Overdue: Any</option>
          <option value="true">Overdue only</option>
          <option value="false">Not overdue</option>
        </select>
      </div>

      {loading ? (
        <Loading />
      ) : data.items.length === 0 ? (
        <EmptyState title="No cases found" description="Try adjusting filters or submit a new complaint." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Case ID</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Institution</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr key={c.id} className="border-b last:border-0 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <Link to={`/cases/${c.id}`} className="font-medium text-navy-700 hover:underline">
                        {c.case_id}
                      </Link>
                      {c.is_overdue && (
                        <span className="ml-1 text-xs text-red-600">●</span>
                      )}
                    </td>
                    <td className="max-w-xs truncate px-4 py-3">{c.title}</td>
                    <td className="px-4 py-3 text-slate-600">{c.institution_name || '—'}</td>
                    <td className="px-4 py-3 text-xs text-slate-500">{c.category}</td>
                    <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                    <td className="px-4 py-3"><PriorityBadge priority={c.priority} /></td>
                    <td className="px-4 py-3 text-slate-500">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, data.total)} of {data.total}
            </span>
            <div className="flex gap-2">
              <button
                className="btn-secondary"
                disabled={page <= 1}
                onClick={() => updateFilter('page', String(page - 1))}
              >
                Previous
              </button>
              <button
                className="btn-secondary"
                disabled={page >= data.pages}
                onClick={() => updateFilter('page', String(page + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
