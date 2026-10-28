import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listNotifications, markRead, markAllRead } from '../services/api'
import Loading, { EmptyState } from '../components/Loading'

export default function Notifications() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = () => {
    listNotifications().then((r) => setItems(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <Loading />

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <button className="btn-secondary text-sm" onClick={() => markAllRead().then(load)}>Mark all read</button>
      </div>
      {items.length === 0 ? (
        <EmptyState title="No notifications" />
      ) : (
        <ul className="space-y-2">
          {items.map((n) => (
            <li
              key={n.id}
              className={`card cursor-pointer transition hover:shadow-md ${!n.is_read ? 'border-l-4 border-l-navy-600 bg-blue-50/30' : ''}`}
              onClick={() => {
                markRead(n.id)
                if (n.case_id) navigate(`/cases/${n.case_id}`)
              }}
            >
              <p className="font-medium">{n.title}</p>
              <p className="mt-1 text-sm text-slate-600">{n.message}</p>
              <p className="mt-2 text-xs text-slate-400">{new Date(n.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
