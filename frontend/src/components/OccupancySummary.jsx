import { Building2, Users, DoorOpen, TrendingUp } from 'lucide-react'

function StatCard({ title, value, subtitle, icon: Icon, trend, color = 'primary' }) {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    green: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    red: 'bg-red-50 text-red-600',
  }

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-2.5 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-3 text-sm ${trend >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
          <TrendingUp className={`w-4 h-4 ${trend < 0 ? 'rotate-180' : ''}`} />
          <span>{trend >= 0 ? '+' : ''}{trend}% from last month</span>
        </div>
      )}
    </div>
  )
}

export default function OccupancySummary({ data }) {
  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="stat-card animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-24 mb-3"></div>
            <div className="h-8 bg-slate-200 rounded w-16"></div>
          </div>
        ))}
      </div>
    )
  }

  const occupancyColor = data.occupancy_rate >= 90 ? 'green' : data.occupancy_rate >= 70 ? 'amber' : 'red'

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Rooms"
        value={data.total_rooms}
        icon={Building2}
        color="primary"
      />
      <StatCard
        title="Occupied"
        value={data.occupied}
        subtitle={`${data.occupancy_rate}% occupancy`}
        icon={Users}
        color="green"
      />
      <StatCard
        title="Vacant"
        value={data.vacant}
        subtitle="Available for booking"
        icon={DoorOpen}
        color={data.vacant > 20 ? 'amber' : 'green'}
      />
      <StatCard
        title="Occupancy Rate"
        value={`${data.occupancy_rate}%`}
        subtitle={`As of ${data.as_of}`}
        icon={TrendingUp}
        color={occupancyColor}
      />
    </div>
  )
}
