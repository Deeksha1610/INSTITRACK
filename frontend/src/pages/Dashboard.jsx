import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText, Clock, AlertTriangle, CheckCircle, Inbox, Users, Building2, Layers
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { getDashboardSummary, getRecentActivity, getWorkload, getTrends } from '../services/api'
import StatCard from '../components/StatCard'
import Loading from '../components/Loading'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const PIE_COLORS = ['#1e3a5f', '#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4', '#84cc16']

export default function Dashboard() {
  const { user } = useAuth()
  const [summary, setSummary] = useState(null)
  const [activity, setActivity] = useState([])
  const [workload, setWorkload] = useState([])
  const [trends, setTrends] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getDashboardSummary(),
      getRecentActivity(),
      user?.role !== 'complainant' ? getWorkload().catch(() => ({ data: [] })) : Promise.resolve({ data: [] }),
      user?.role !== 'complainant' ? getTrends().catch(() => ({ data: null })) : Promise.resolve({ data: null }),
    ])
      .then(([s, a, w, t]) => {
        setSummary(s.data)
        setActivity(a.data)
        setWorkload(w.data || [])
        setTrends(t.data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user])

  if (loading) return <Loading />

  const role = user?.role

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          {role === 'complainant' && 'My Complaints'}
          {role === 'bureau_officer' && 'Bureau Work Queue'}
          {role === 'central_monitoring' && 'Central Monitoring Dashboard'}
          {role === 'super_admin' && 'System Administration'}
          {role === 'auditor' && 'Audit Overview'}
        </h1>
        <p className="text-sm text-slate-500">Welcome, {user?.full_name}</p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {role === 'complainant' && (
          <>
            <StatCard title="Total Submitted" value={summary?.total_cases} icon={FileText} color="navy" />
            <StatCard title="In Progress" value={summary?.assigned_in_progress} icon={Clock} color="amber" />
            <StatCard title="Needs Your Info" value={summary?.needs_information} icon={Inbox} color="violet" />
            <StatCard title="Resolved / Closed" value={summary?.resolved_closed} icon={CheckCircle} color="emerald" />
          </>
        )}
        {role === 'bureau_officer' && (
          <>
            <StatCard title="My Assigned" value={summary?.my_assigned} icon={FileText} color="navy" />
            <StatCard title="Awaiting Ack" value={summary?.awaiting_acknowledgement} icon={Inbox} color="blue" />
            <StatCard title="In Progress" value={summary?.assigned_in_progress} icon={Clock} color="amber" />
            <StatCard title="Overdue" value={summary?.overdue} icon={AlertTriangle} color="red" />
            <StatCard title="Resolution Pending" value={summary?.resolution_pending_review} icon={CheckCircle} color="violet" />
            <StatCard title="Coordination" value={summary?.pending_coordination} icon={Layers} color="blue" />
          </>
        )}
        {(role === 'central_monitoring' || role === 'super_admin' || role === 'auditor') && (
          <>
            <StatCard title="Total Cases" value={summary?.total_cases} icon={FileText} color="navy" />
            <StatCard title="Awaiting Review" value={summary?.new_awaiting_review} icon={Inbox} color="blue" />
            <StatCard title="Unassigned" value={summary?.accepted_unassigned} icon={Clock} color="amber" />
            <StatCard title="In Progress" value={summary?.assigned_in_progress} icon={Layers} color="violet" />
            <StatCard title="Overdue" value={summary?.overdue} icon={AlertTriangle} color="red" />
            <StatCard title="Closed / Rejected" value={summary?.resolved_closed} icon={CheckCircle} color="emerald" />
            {role === 'super_admin' && (
              <>
                <StatCard title="Users" value={summary?.total_users} icon={Users} color="navy" />
                <StatCard title="Institutions" value={summary?.total_institutions} icon={Building2} color="blue" />
              </>
            )}
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent activity */}
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">Recent Activity</h2>
          {activity.length === 0 ? (
            <p className="text-sm text-slate-400">No recent activity</p>
          ) : (
            <ul className="space-y-3">
              {activity.slice(0, 8).map((a) => (
                <li key={a.id} className="flex items-start gap-3 border-b border-slate-100 pb-3 last:border-0">
                  <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-navy-500" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">
                      <span className="font-medium">{a.actor_name}</span>
                      {' · '}
                      <span className="text-slate-600">{a.action.replace(/_/g, ' ')}</span>
                      {a.case_id && (
                        <>
                          {' · '}
                          <Link to={`/cases/${a.case_db_id}`} className="text-navy-700 hover:underline">
                            {a.case_id}
                          </Link>
                        </>
                      )}
                    </p>
                    <p className="text-xs text-slate-400">
                      {new Date(a.created_at).toLocaleString()}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Workload / Charts */}
        {workload.length > 0 && (
          <div className="card">
            <h2 className="mb-4 text-lg font-semibold">Bureau Workload</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={workload}>
                <XAxis dataKey="code" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="case_count" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {trends?.by_status && (
          <div className="card">
            <h2 className="mb-4 text-lg font-semibold">Cases by Status</h2>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={trends.by_status}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ status, count }) => `${status}: ${count}`}
                  labelLine={false}
                >
                  {trends.by_status.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {trends?.by_category && (
          <div className="card">
            <h2 className="mb-4 text-lg font-semibold">Cases by Category</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={trends.by_category} layout="vertical" margin={{ left: 20 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="category" width={120} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {role === 'complainant' && (
        <div className="flex justify-center">
          <Link to="/submit" className="btn-primary">
            Submit New Complaint
          </Link>
        </div>
      )}
    </div>
  )
}
