import { STATUS_COLORS, PRIORITY_COLORS } from '../utils/constants'

export function StatusBadge({ status }) {
  const cls = STATUS_COLORS[status] || 'bg-slate-100 text-slate-700'
  return <span className={`badge ${cls}`}>{status?.replace(/_/g, ' ')}</span>
}

export function PriorityBadge({ priority }) {
  const cls = PRIORITY_COLORS[priority] || 'bg-slate-100 text-slate-700'
  return <span className={`badge ${cls}`}>{priority}</span>
}
