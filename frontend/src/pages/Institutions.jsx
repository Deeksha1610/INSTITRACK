import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listInstitutions, getInstitutionStats } from '../services/api'
import Loading, { EmptyState } from '../components/Loading'

export default function Institutions() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    listInstitutions().then((r) => setItems(r.data)).finally(() => setLoading(false))
  }, [])

  const viewStats = async (inst) => {
    setSelected(inst)
    const r = await getInstitutionStats(inst.id)
    setStats(r.data)
  }

  if (loading) return <Loading />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Institution Directory</h1>
      <p className="text-sm text-slate-500">Fictional demonstration institutions for SIH.</p>
      {items.length === 0 ? (
        <EmptyState title="No institutions" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="overflow-x-auto rounded-xl border bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead className="border-b bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3 text-left">ID</th>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">State</th>
                  <th className="px-4 py-3 text-left"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((i) => (
                  <tr key={i.id} className="border-b hover:bg-slate-50">
                    <td className="px-4 py-2 font-mono text-xs">{i.institution_id}</td>
                    <td className="px-4 py-2">{i.name}</td>
                    <td className="px-4 py-2 text-slate-500">{i.state}</td>
                    <td className="px-4 py-2">
                      <button className="text-navy-700 hover:underline" onClick={() => viewStats(i)}>Stats</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {stats && (
            <div className="card">
              <h2 className="text-lg font-semibold">{stats.institution.name}</h2>
              <p className="text-sm text-slate-500">{stats.institution.institution_id} · {stats.institution.city}, {stats.institution.state}</p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-navy-50 p-3 text-center">
                  <p className="text-2xl font-bold text-navy-900">{stats.total_cases}</p>
                  <p className="text-xs text-slate-500">Total</p>
                </div>
                <div className="rounded-lg bg-amber-50 p-3 text-center">
                  <p className="text-2xl font-bold text-amber-800">{stats.open_cases}</p>
                  <p className="text-xs text-slate-500">Open</p>
                </div>
                <div className="rounded-lg bg-emerald-50 p-3 text-center">
                  <p className="text-2xl font-bold text-emerald-800">{stats.resolved_cases}</p>
                  <p className="text-xs text-slate-500">Resolved</p>
                </div>
                <div className="rounded-lg bg-red-50 p-3 text-center">
                  <p className="text-2xl font-bold text-red-800">{stats.overdue_cases}</p>
                  <p className="text-xs text-slate-500">Overdue</p>
                </div>
              </div>
              {Object.keys(stats.category_breakdown || {}).length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium">Category breakdown</h3>
                  <ul className="mt-2 space-y-1 text-sm">
                    {Object.entries(stats.category_breakdown).map(([k, v]) => (
                      <li key={k} className="flex justify-between"><span>{k}</span><span className="font-medium">{v}</span></li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
