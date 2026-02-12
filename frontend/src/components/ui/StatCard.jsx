import { TrendingUp } from 'lucide-react'

const colorConfig = {
  primary: {
    bg: 'bg-gradient-to-br from-sky-50 to-sky-100',
    icon: 'bg-sky-500 text-white',
    text: 'text-sky-600',
  },
  green: {
    bg: 'bg-gradient-to-br from-emerald-50 to-emerald-100',
    icon: 'bg-emerald-500 text-white',
    text: 'text-emerald-600',
  },
  amber: {
    bg: 'bg-gradient-to-br from-amber-50 to-amber-100',
    icon: 'bg-amber-500 text-white',
    text: 'text-amber-600',
  },
  red: {
    bg: 'bg-gradient-to-br from-red-50 to-red-100',
    icon: 'bg-red-500 text-white',
    text: 'text-red-600',
  },
  blue: {
    bg: 'bg-gradient-to-br from-blue-50 to-blue-100',
    icon: 'bg-blue-500 text-white',
    text: 'text-blue-600',
  },
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'primary',
}) {
  const colors = colorConfig[color] || colorConfig.primary

  return (
    <div className={`rounded-xl border border-slate-200 p-5 shadow-sm ${colors.bg}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-600">{title}</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">{value}</p>
          {subtitle && (
            <p className={`text-sm mt-1 ${colors.text}`}>{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-xl ${colors.icon}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      {trend !== undefined && (
        <div
          className={`flex items-center gap-1 mt-4 text-sm font-medium ${
            trend >= 0 ? 'text-emerald-600' : 'text-red-600'
          }`}
        >
          <TrendingUp className={`w-4 h-4 ${trend < 0 ? 'rotate-180' : ''}`} />
          <span>
            {trend >= 0 ? '+' : ''}
            {trend}% from last month
          </span>
        </div>
      )}
    </div>
  )
}
