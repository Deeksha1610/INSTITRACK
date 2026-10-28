import { useState, useEffect } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FileText, Building2, Users, Bell, LogOut, Menu, X,
  ClipboardList, GitBranch, BarChart3, Shield, Settings, PlusCircle, Search
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { unreadCount, listNotifications, markRead, markAllRead } from '../services/api'
import { ROLE_LABELS } from '../utils/constants'

const NAV = {
  complainant: [
    { to: '/dashboard', label: 'My Cases', icon: LayoutDashboard },
    { to: '/submit', label: 'Submit Complaint', icon: PlusCircle },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ],
  central_monitoring: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/cases', label: 'All Cases', icon: FileText },
    { to: '/cases?status=SUBMITTED', label: 'Review Queue', icon: ClipboardList },
    { to: '/institutions', label: 'Institutions', icon: Building2 },
    { to: '/coordination', label: 'Coordination', icon: GitBranch },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/reports', label: 'Reports', icon: FileText },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ],
  bureau_officer: [
    { to: '/dashboard', label: 'Work Queue', icon: LayoutDashboard },
    { to: '/cases', label: 'My Cases', icon: FileText },
    { to: '/coordination', label: 'Coordination', icon: GitBranch },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ],
  super_admin: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/cases', label: 'All Cases', icon: FileText },
    { to: '/institutions', label: 'Institutions', icon: Building2 },
    { to: '/users', label: 'Users', icon: Users },
    { to: '/bureaus', label: 'Bureaus', icon: Settings },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/reports', label: 'Reports', icon: FileText },
    { to: '/audit', label: 'Audit Logs', icon: Shield },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ],
  auditor: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/cases', label: 'Case Records', icon: FileText },
    { to: '/audit', label: 'Audit Logs', icon: Shield },
    { to: '/reports', label: 'Reports', icon: BarChart3 },
  ],
}

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const [showNotifs, setShowNotifs] = useState(false)
  const [notifs, setNotifs] = useState([])

  const navItems = NAV[user?.role] || NAV.complainant

  useEffect(() => {
    const load = () => {
      unreadCount().then((r) => setUnread(r.data.count)).catch(() => {})
    }
    load()
    const iv = setInterval(load, 30000)
    return () => clearInterval(iv)
  }, [])

  const openNotifs = async () => {
    setShowNotifs(!showNotifs)
    if (!showNotifs) {
      try {
        const r = await listNotifications()
        setNotifs(r.data)
      } catch {}
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-navy-950 text-white transition-transform lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center gap-2 border-b border-navy-800 px-5">
          <Shield className="h-7 w-7 text-blue-300" />
          <div>
            <div className="text-lg font-bold tracking-tight">INSTITRACK</div>
            <div className="text-[10px] text-navy-300">Case Tracking Platform</div>
          </div>
          <button className="ml-auto lg:hidden" onClick={() => setSidebarOpen(false)}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="space-y-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? 'bg-navy-800 text-white' : 'text-navy-200 hover:bg-navy-900 hover:text-white'
                }`
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 border-t border-navy-800 p-4">
          <div className="mb-2 truncate text-xs text-navy-300">{user?.full_name}</div>
          <div className="mb-3 text-[10px] uppercase tracking-wider text-navy-400">
            {ROLE_LABELS[user?.role] || user?.role}
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-navy-200 hover:bg-navy-900"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-slate-200 bg-white px-4 shadow-sm">
          <button className="lg:hidden" onClick={() => setSidebarOpen(true)}>
            <Menu className="h-6 w-6 text-slate-600" />
          </button>
          <div className="flex-1">
            <p className="hidden text-sm text-slate-500 sm:block">
              One Institution. Connected Cases. Smarter Decisions.
            </p>
          </div>
          <div className="relative">
            <button
              onClick={openNotifs}
              className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100"
            >
              <Bell className="h-5 w-5" />
              {unread > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                  {unread > 9 ? '9+' : unread}
                </span>
              )}
            </button>
            {showNotifs && (
              <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-slate-200 bg-white shadow-xl">
                <div className="flex items-center justify-between border-b px-4 py-2">
                  <span className="text-sm font-semibold">Notifications</span>
                  <button
                    className="text-xs text-navy-600 hover:underline"
                    onClick={() => markAllRead().then(() => { setUnread(0); setNotifs((n) => n.map((x) => ({ ...x, is_read: true }))) })}
                  >
                    Mark all read
                  </button>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifs.length === 0 ? (
                    <p className="p-4 text-center text-sm text-slate-400">No notifications</p>
                  ) : (
                    notifs.slice(0, 10).map((n) => (
                      <button
                        key={n.id}
                        className={`block w-full border-b px-4 py-3 text-left hover:bg-slate-50 ${!n.is_read ? 'bg-blue-50/50' : ''}`}
                        onClick={() => {
                          markRead(n.id)
                          setShowNotifs(false)
                          if (n.case_id) navigate(`/cases/${n.case_id}`)
                        }}
                      >
                        <p className="text-sm font-medium text-slate-800">{n.title}</p>
                        <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{n.message}</p>
                      </button>
                    ))
                  )}
                </div>
                <Link
                  to="/notifications"
                  className="block border-t py-2 text-center text-sm text-navy-600 hover:bg-slate-50"
                  onClick={() => setShowNotifs(false)}
                >
                  View all
                </Link>
              </div>
            )}
          </div>
        </header>
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  )
}
