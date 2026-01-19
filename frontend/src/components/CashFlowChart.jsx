import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, Line } from 'recharts'
import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react'

function formatCurrency(value) {
  if (value >= 1000000) {
    return `£${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `£${(value / 1000).toFixed(0)}K`
  }
  return `£${value}`
}

function SummaryCard({ title, value, trend, icon: Icon, color }) {
  const colorClasses = {
    green: 'bg-emerald-50 text-emerald-600',
    red: 'bg-red-50 text-red-600',
    blue: 'bg-blue-50 text-blue-600',
  }

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="text-xl font-bold text-slate-900 mt-1">{formatCurrency(value)}</p>
        </div>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
    </div>
  )
}

export default function CashFlowChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="stat-card animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-24 mb-3"></div>
              <div className="h-8 bg-slate-200 rounded w-20"></div>
            </div>
          ))}
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Monthly Cash Flow</h3>
          <div className="h-72 flex items-center justify-center text-slate-500">
            No cash flow data available. Import contracts first.
          </div>
        </div>
      </div>
    )
  }

  // Calculate totals for summary cards
  const totalInflows = data.reduce((sum, d) => sum + (d.inflows || 0), 0)
  const totalOutflows = data.reduce((sum, d) => sum + Math.abs(d.outflows || 0), 0)
  const netCashFlow = totalInflows - totalOutflows

  // Format data for chart
  const chartData = data.map(d => ({
    month: d.month,
    Inflows: d.inflows || 0,
    Outflows: Math.abs(d.outflows || 0),
    'Net Cash Flow': d.net_cashflow || 0,
    'Running Balance': d.running_balance || 0,
  }))

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard
          title="Total Inflows (12 mo)"
          value={totalInflows}
          icon={TrendingUp}
          color="green"
        />
        <SummaryCard
          title="Total Outflows (12 mo)"
          value={totalOutflows}
          icon={TrendingDown}
          color="red"
        />
        <SummaryCard
          title="Net Cash Flow"
          value={netCashFlow}
          icon={DollarSign}
          color={netCashFlow >= 0 ? 'green' : 'red'}
        />
      </div>

      {/* Main Chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">Monthly Cash Flow</h3>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={{ stroke: '#e2e8f0' }}
              />
              <YAxis
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={{ stroke: '#e2e8f0' }}
                tickFormatter={formatCurrency}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                }}
                formatter={(value) => formatCurrency(value)}
              />
              <Legend />
              <Bar dataKey="Inflows" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Outflows" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              <Line
                type="monotone"
                dataKey="Running Balance"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Net Cash Flow Area Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Net Cash Flow Trend</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={formatCurrency} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Area
                type="monotone"
                dataKey="Net Cash Flow"
                stroke="#0ea5e9"
                fill="#e0f2fe"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
