export default function StatCard({ title, value, icon: Icon, color = 'navy', subtitle }) {
  const colorMap = {
    navy: 'bg-navy-50 text-navy-700 border-navy-100',
    blue: 'bg-blue-50 text-blue-700 border-blue-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    red: 'bg-red-50 text-red-700 border-red-100',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    violet: 'bg-violet-50 text-violet-700 border-violet-100',
  }
  return (
    <div className={`card border ${colorMap[color] || colorMap.navy}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium opacity-80">{title}</p>
          <p className="mt-1 text-2xl font-bold">{value ?? '—'}</p>
          {subtitle && <p className="mt-0.5 text-xs opacity-70">{subtitle}</p>}
        </div>
        {Icon && (
          <div className="rounded-lg bg-white/60 p-2">
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  )
}
