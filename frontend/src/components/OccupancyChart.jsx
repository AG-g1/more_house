import { useState, useEffect, useCallback } from 'react'
import {
  AreaChart,
  BarChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { TrendingUp, ArrowUpDown } from 'lucide-react'
import PeriodSelector, { getPeriodConfig } from './ui/PeriodSelector'
import { API_BASE } from '../config'
const TOTAL_CAPACITY = 120

export default function OccupancyChart({ currentOccupancy = 0 }) {
  const [period, setPeriod] = useState('12m')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    const config = getPeriodConfig(period)

    try {
      let response
      if (config.granularity === 'monthly') {
        const today = new Date()
        const endDate = new Date(today)
        endDate.setMonth(endDate.getMonth() + config.months)
        const startMonth = today.toISOString().slice(0, 7)
        const endMonth = endDate.toISOString().slice(0, 7)
        response = await fetch(
          `${API_BASE}/occupancy/monthly?start_month=${startMonth}&end_month=${endMonth}`
        )
      } else {
        response = await fetch(
          `${API_BASE}/occupancy/weekly?weeks=${config.weeks}`
        )
      }

      if (response.ok) {
        const result = await response.json()
        setData(result)
      }
    } catch (err) {
      console.error('Failed to fetch occupancy data:', err)
    } finally {
      setLoading(false)
    }
  }, [period])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const config = getPeriodConfig(period)
  const isMonthly = config.granularity === 'monthly'

  // Transform data for both charts
  // Use start_occupancy for the current period, then calculate forward
  const chartData = data.map((d, index) => {
    const label = isMonthly
      ? formatMonthLabel(d.month)
      : formatWeekLabel(d.week_start)

    // For the first month, use the API's start_occupancy (which is current occupancy)
    // For subsequent months, calculate based on cumulative changes but cap at capacity
    let occupancy
    if (index === 0) {
      occupancy = d.start_occupancy ?? currentOccupancy
    } else {
      // Calculate cumulative occupancy from start
      let cumulative = data[0].start_occupancy ?? currentOccupancy
      for (let i = 0; i <= index; i++) {
        cumulative += (data[i].move_ins || 0) - (data[i].move_outs || 0)
      }
      // Cap at capacity (can't have more than 120 rooms occupied)
      occupancy = Math.min(Math.max(cumulative, 0), TOTAL_CAPACITY)
    }

    return {
      label,
      occupancy,
      moveIns: d.move_ins || 0,
      moveOuts: -(d.move_outs || 0), // Negative for visual effect
    }
  })

  // Calculate max movement for Y-axis domain
  const maxMovement = Math.max(
    ...data.map(d => Math.max(d.move_ins || 0, d.move_outs || 0)),
    10
  )

  const OccupancyTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-slate-800 mb-1">{label}</p>
          <p className="text-sm text-blue-600">
            Occupancy: <span className="font-medium">{payload[0].value} rooms</span>
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {((payload[0].value / TOTAL_CAPACITY) * 100).toFixed(1)}% of capacity
          </p>
        </div>
      )
    }
    return null
  }

  const MovementTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const moveIns = payload.find(p => p.dataKey === 'moveIns')?.value || 0
      const moveOuts = Math.abs(payload.find(p => p.dataKey === 'moveOuts')?.value || 0)
      const net = moveIns - moveOuts
      return (
        <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-slate-800 mb-2">{label}</p>
          <div className="space-y-1 text-sm">
            <p className="text-emerald-600">
              Move-ins: <span className="font-medium">+{moveIns}</span>
            </p>
            <p className="text-rose-600">
              Move-outs: <span className="font-medium">-{moveOuts}</span>
            </p>
            <div className="border-t pt-1 mt-1">
              <p className={net >= 0 ? 'text-emerald-700' : 'text-rose-700'}>
                Net change: <span className="font-semibold">{net >= 0 ? '+' : ''}{net}</span>
              </p>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className="card">
        <div className="h-[600px] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="h-[600px] flex items-center justify-center text-slate-500">
          No data available. Import contracts first.
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">
            Occupancy Forecast
          </h3>
          <p className="text-sm text-slate-500">
            Current: {currentOccupancy} / {TOTAL_CAPACITY} rooms ({((currentOccupancy / TOTAL_CAPACITY) * 100).toFixed(0)}%)
          </p>
        </div>
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>

      {/* Top Chart: Occupancy Status */}
      <div className="mb-2">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-blue-500" />
          <span className="text-sm font-medium text-slate-700">Occupancy Level</span>
        </div>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="occupancyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                hide={true}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                domain={[0, TOTAL_CAPACITY + 10]}
                ticks={[0, 30, 60, 90, 120]}
                width={40}
              />
              <Tooltip content={<OccupancyTooltip />} />
              <ReferenceLine
                y={TOTAL_CAPACITY}
                stroke="#94a3b8"
                strokeDasharray="5 5"
                label={{
                  value: 'Capacity',
                  position: 'right',
                  fill: '#94a3b8',
                  fontSize: 10,
                }}
              />
              <Area
                type="monotone"
                dataKey="occupancy"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#occupancyGradient)"
                dot={{ r: 3, fill: '#3b82f6', strokeWidth: 0 }}
                activeDot={{ r: 5, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-slate-100 my-4"></div>

      {/* Bottom Chart: Movement (Drivers) */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <ArrowUpDown className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-700">Monthly Movement</span>
          <span className="text-xs text-slate-400 ml-2">(What's driving the change)</span>
        </div>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 30 }}
              barCategoryGap="20%"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                angle={-45}
                textAnchor="end"
                height={50}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                domain={[-maxMovement - 5, maxMovement + 5]}
                width={40}
              />
              <Tooltip content={<MovementTooltip />} />
              <ReferenceLine y={0} stroke="#cbd5e1" />
              <Bar
                dataKey="moveIns"
                fill="#10b981"
                radius={[4, 4, 0, 0]}
                name="Move-ins"
              />
              <Bar
                dataKey="moveOuts"
                fill="#ef4444"
                radius={[0, 0, 4, 4]}
                name="Move-outs"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-center gap-8 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span className="text-slate-600">Occupancy</span>
        </div>
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

function formatMonthLabel(month) {
  if (!month) return ''
  const [year, m] = month.split('-')
  const date = new Date(year, parseInt(m) - 1)
  return date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })
}

function formatWeekLabel(weekStart) {
  if (!weekStart) return ''
  const date = new Date(weekStart)
  return date.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })
}
