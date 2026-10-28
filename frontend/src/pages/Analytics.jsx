import { useEffect, useState } from 'react'
import { getTrends, getWorkload } from '../services/api'
import Loading from '../components/Loading'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Legend } from 'recharts'

export default function Analytics() {
  const [trends, setTrends] = useState(null)
  const [workload, setWorkload] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getTrends(60), getWorkload()])
      .then(([t, w]) => { setTrends(t.data); setWorkload(w.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>
      <p className="text-sm text-slate-500">Charts driven by live database data.</p>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 font-semibold">Submissions Over Time</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trends?.submitted_over_time || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#1e3a5f" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">Closures Over Time</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trends?.closed_over_time || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">By Category</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trends?.by_category || []} layout="vertical" margin={{ left: 10 }}>
              <XAxis type="number" />
              <YAxis type="category" dataKey="category" width={130} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">Bureau Workload</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={workload}>
              <XAxis dataKey="code" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="case_count" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
