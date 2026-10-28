export const STATUS_COLORS = {
  SUBMITTED: 'bg-blue-100 text-blue-800',
  UNDER_REVIEW: 'bg-indigo-100 text-indigo-800',
  ACCEPTED: 'bg-cyan-100 text-cyan-800',
  ASSIGNED: 'bg-violet-100 text-violet-800',
  IN_PROGRESS: 'bg-amber-100 text-amber-800',
  NEEDS_INFORMATION: 'bg-orange-100 text-orange-800',
  RETURNED: 'bg-pink-100 text-pink-800',
  REJECTED: 'bg-red-100 text-red-800',
  RESOLUTION_SUBMITTED: 'bg-teal-100 text-teal-800',
  ESCALATED: 'bg-rose-100 text-rose-800',
  CLOSED: 'bg-emerald-100 text-emerald-800',
  REOPENED: 'bg-slate-100 text-slate-800',
}

export const PRIORITY_COLORS = {
  LOW: 'bg-slate-100 text-slate-700',
  MEDIUM: 'bg-blue-100 text-blue-700',
  HIGH: 'bg-orange-100 text-orange-700',
  CRITICAL: 'bg-red-100 text-red-700',
}

export const CATEGORIES = [
  'Academic / Examination Issues',
  'Admission-related Issues',
  'Institutional Facilities',
  'Fee-related Issues',
  'Faculty / Staff Issues',
  'Student Grievances',
  'Infrastructure Issues',
  'Regulatory / Compliance Concerns',
  'Other',
]

export const ROLE_LABELS = {
  complainant: 'Complainant',
  super_admin: 'Super Admin',
  central_monitoring: 'Central Monitoring Officer',
  bureau_officer: 'Bureau Officer',
  auditor: 'Auditor',
}

export const DEMO_CREDENTIALS = [
  { role: 'Complainant', username: 'complainant1', password: 'Student@123' },
  { role: 'Central Monitoring', username: 'monitor1', password: 'Monitor@123' },
  { role: 'Bureau Officer (Facilities)', username: 'officer_faci', password: 'Officer@123' },
  { role: 'Bureau Officer (Academic)', username: 'officer_acad', password: 'Officer@123' },
  { role: 'Super Admin', username: 'admin', password: 'Admin@123' },
  { role: 'Auditor', username: 'auditor1', password: 'Auditor@123' },
]
