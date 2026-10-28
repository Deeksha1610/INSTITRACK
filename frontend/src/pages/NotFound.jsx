import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <h1 className="text-6xl font-bold text-navy-900">404</h1>
      <p className="mt-2 text-slate-600">Page not found</p>
      <Link to="/dashboard" className="btn-primary mt-6">Go to Dashboard</Link>
    </div>
  )
}
