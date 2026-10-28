import { useEffect, useState } from 'react'
import { listBureaus, getRoutingRules } from '../services/api'
import Loading from '../components/Loading'

export default function Bureaus() {
  const [bureaus, setBureaus] = useState([])
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([listBureaus(), getRoutingRules()])
      .then(([b, r]) => { setBureaus(b.data); setRules(r.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Bureaus / Cells Configuration</h1>
      <p className="text-sm text-slate-500">Demonstration bureaus and category routing rules (not official AICTE structures).</p>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {bureaus.map((b) => (
          <div key={b.id} className="card">
            <p className="font-mono text-xs text-navy-600">{b.code}</p>
            <p className="font-semibold">{b.name}</p>
            <p className="mt-1 text-sm text-slate-500">{b.description}</p>
          </div>
        ))}
      </div>
      <div className="card">
        <h2 className="mb-3 font-semibold">Category → Bureau Routing Rules</h2>
        <table className="w-full text-sm">
          <thead className="border-b text-xs uppercase text-slate-500">
            <tr>
              <th className="py-2 text-left">Category</th>
              <th className="py-2 text-left">Recommended Bureau</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.id} className="border-b">
                <td className="py-2">{r.category}</td>
                <td className="py-2">{r.bureau_name} ({r.bureau_code})</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
