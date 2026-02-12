import { Building2, Users, PoundSterling, FileText } from 'lucide-react'
import StatCard from './ui/StatCard'

export default function OccupancySummary({ data }) {
  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-slate-200 bg-white p-5 animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-24 mb-3"></div>
            <div className="h-10 bg-slate-200 rounded w-16"></div>
          </div>
        ))}
      </div>
    )
  }

  const formatCurrency = (value) => {
    if (value >= 1000000) {
      return `£${(value / 1000000).toFixed(2)}M`
    }
    if (value >= 1000) {
      return `£${(value / 1000).toFixed(0)}K`
    }
    return `£${value}`
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Occupancy"
        value={`${data.occupied} / ${data.total_rooms}`}
        subtitle={`${data.occupancy_rate}% occupied`}
        icon={Users}
        color={data.occupancy_rate >= 85 ? 'green' : data.occupancy_rate >= 70 ? 'amber' : 'red'}
      />
      <StatCard
        title="Vacant Rooms"
        value={data.vacant}
        subtitle="Available for booking"
        icon={Building2}
        color={data.vacant <= 10 ? 'green' : data.vacant <= 20 ? 'amber' : 'red'}
      />
      <StatCard
        title="Avg Weekly Rent"
        value={`£${data.avg_weekly_rent?.toLocaleString() || 0}`}
        subtitle="Per occupied room"
        icon={PoundSterling}
        color="primary"
      />
      <StatCard
        title="Net Income Signed"
        value={formatCurrency(data.total_signed_value || 0)}
        subtitle={`${data.contract_count || 0} contracts`}
        icon={FileText}
        color="green"
      />
    </div>
  )
}
