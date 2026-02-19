import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { PoundSterling, TrendingUp, Calendar, CheckCircle } from 'lucide-react'
import { API_BASE } from '../config'

function formatCurrency(value) {
  if (value >= 1000000) {
    return `£${(value / 1000000).toFixed(2)}M`
  }
  if (value >= 1000) {
    return `£${(value / 1000).toFixed(0)}K`
  }
  return `£${value?.toFixed(0) || 0}`
}

function formatMonth(monthStr) {
  if (!monthStr) return ''
  const [year, month] = monthStr.split('-')
  const date = new Date(year, parseInt(month) - 1)
  return date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })
}

function formatMonthLong(monthStr) {
  if (!monthStr) return ''
  const [year, month] = monthStr.split('-')
  const date = new Date(year, parseInt(month) - 1)
  return date.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
}

export default function CashFlowPage() {
  const [data, setData] = useState([])
  const [scheduleData, setScheduleData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [monthlyRes, scheduleRes] = await Promise.all([
        fetch(`${API_BASE}/cashflow/monthly`),
        fetch(`${API_BASE}/cashflow/payments/schedule`)
      ])

      if (monthlyRes.ok) setData(await monthlyRes.json())
      if (scheduleRes.ok) setScheduleData(await scheduleRes.json())
    } catch (err) {
      console.error('Failed to fetch cashflow data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Calculate totals from schedule data
  const totalExpected = scheduleData.reduce((sum, d) => sum + (parseFloat(d.total_expected) || 0), 0)
  const totalPaid = scheduleData.reduce((sum, d) => sum + (parseFloat(d.total_paid) || 0), 0)
  const totalOutstanding = scheduleData.reduce((sum, d) => sum + (parseFloat(d.outstanding) || 0), 0)
  const totalPayments = scheduleData.reduce((sum, d) => sum + (d.num_payments || 0), 0)

  // Format data for chart
  const chartData = data.map(d => ({
    month: formatMonth(d.month),
    'Expected Income': d.expected_inflows || 0,
  }))

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-slate-800 mb-1">{label}</p>
          <p className="text-sm text-emerald-600">
            Expected: <span className="font-medium">{formatCurrency(payload[0].value)}</span>
          </p>
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Cash Flow</h1>
          <p className="text-slate-500 mt-1">Expected income by month</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Cash Flow</h1>
        <p className="text-slate-500 mt-1">Payment schedule and expected income</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Total Expected</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{formatCurrency(totalExpected)}</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <TrendingUp className="w-5 h-5 text-slate-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Already Paid</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(totalPaid)}</p>
            </div>
            <div className="p-3 bg-emerald-50 rounded-lg">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Outstanding</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">{formatCurrency(totalOutstanding)}</p>
            </div>
            <div className="p-3 bg-amber-50 rounded-lg">
              <PoundSterling className="w-5 h-5 text-amber-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Total Payments</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{totalPayments}</p>
              <p className="text-xs text-slate-400 mt-1">installments scheduled</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-6">Expected Income by Month</h3>

        {data.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-slate-500">
            No cash flow data available. Import contracts first.
          </div>
        ) : (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatCurrency}
                  width={70}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="Expected Income"
                  fill="#10b981"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={60}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Monthly Payment Schedule Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">Monthly Payment Schedule</h2>
          <p className="text-sm text-slate-500">Scheduled installments by month</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50">
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Month</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">Payments</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Expected</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Paid</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Outstanding</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">Progress</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {scheduleData.map((row, idx) => {
                const expected = parseFloat(row.total_expected) || 0
                const paid = parseFloat(row.total_paid) || 0
                const outstanding = parseFloat(row.outstanding) || 0
                const progress = expected > 0 ? (paid / expected) * 100 : 0

                return (
                  <tr key={row.month} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                    <td className="px-6 py-3 whitespace-nowrap text-sm font-medium text-slate-900">
                      {formatMonthLong(row.month)}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-center text-slate-600">
                      {row.num_payments}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-right text-slate-900">
                      {formatCurrency(expected)}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-right text-emerald-600 font-medium">
                      {formatCurrency(paid)}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-right">
                      {outstanding > 0 ? (
                        <span className="text-amber-600 font-medium">{formatCurrency(outstanding)}</span>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-24 bg-slate-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${progress >= 100 ? 'bg-emerald-500' : 'bg-blue-500'}`}
                            style={{ width: `${Math.min(progress, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500 w-10">{progress.toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
            <tfoot className="bg-slate-100 font-semibold">
              <tr>
                <td className="px-6 py-3 text-sm text-slate-900">Total</td>
                <td className="px-6 py-3 text-sm text-center text-slate-900">{totalPayments}</td>
                <td className="px-6 py-3 text-sm text-right text-slate-900">{formatCurrency(totalExpected)}</td>
                <td className="px-6 py-3 text-sm text-right text-emerald-600">{formatCurrency(totalPaid)}</td>
                <td className="px-6 py-3 text-sm text-right text-amber-600">{formatCurrency(totalOutstanding)}</td>
                <td className="px-6 py-3 text-sm text-center text-slate-600">
                  {totalExpected > 0 ? ((totalPaid / totalExpected) * 100).toFixed(0) : 0}%
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
        {scheduleData.length === 0 && (
          <div className="px-6 py-8 text-center text-slate-500">
            No payment schedule data available
          </div>
        )}
      </div>
    </div>
  )
}
