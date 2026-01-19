import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Calendar } from 'lucide-react'

export default function OccupancyChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900">Monthly Occupancy Movement</h3>
        </div>
        <div className="h-64 flex items-center justify-center text-slate-500">
          No data available. Import contracts first.
        </div>
      </div>
    )
  }

  // Format data for chart
  const chartData = data.map(d => ({
    month: d.month,
    'Move-ins': d.move_ins,
    'Move-outs': -d.move_outs, // Negative for visual effect
    'Net': d.net_change,
  }))

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900">Monthly Occupancy Movement</h3>
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12, fill: '#64748b' }}
              tickLine={{ stroke: '#e2e8f0' }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#64748b' }}
              tickLine={{ stroke: '#e2e8f0' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
              }}
              formatter={(value, name) => [Math.abs(value), name]}
            />
            <Legend />
            <ReferenceLine y={0} stroke="#94a3b8" />
            <Bar dataKey="Move-ins" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Move-outs" fill="#f43f5e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-emerald-500"></div>
          <span className="text-slate-600">Move-ins</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-rose-500"></div>
          <span className="text-slate-600">Move-outs</span>
        </div>
      </div>
    </div>
  )
}
