import { useState, useEffect } from 'react'
import { Eye, FileSignature, ChevronDown, ChevronUp } from 'lucide-react'
import { API_BASE } from '../config'
const PERIODS = ['1d', '3d', '7d', '1m', '3m']
const PERIOD_LABELS = { '1d': '1 Day', '3d': '3 Days', '7d': '7 Days', '1m': '1 Month', '3m': '3 Months' }

export default function ActivityTable() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expandedPeriod, setExpandedPeriod] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/activity/summary`)
      .then(res => res.ok ? res.json() : null)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-48 mb-4"></div>
        <div className="h-20 bg-slate-200 rounded"></div>
      </div>
    )
  }

  if (!data) return null

  const formatDate = (d) => {
    if (!d) return '—'
    return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  const togglePeriod = (period) => {
    setExpandedPeriod(expandedPeriod === period ? null : period)
  }

  const contracts = data.contracts || {}
  const expandedContracts = expandedPeriod ? (contracts[expandedPeriod]?.contracts || []) : []

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200">
        <h2 className="text-lg font-semibold text-slate-900">Recent Activity</h2>
        <p className="text-sm text-slate-500">Viewings and contracts from Monday CRM</p>
      </div>

      <table className="w-full">
        <thead>
          <tr className="bg-slate-50">
            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Metric</th>
            {PERIODS.map(p => (
              <th key={p} className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">
                {PERIOD_LABELS[p]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {/* Viewings row */}
          <tr className="bg-white">
            <td className="px-6 py-3.5 text-sm text-slate-900">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-blue-500" />
                <span className="font-medium">Viewings</span>
              </div>
            </td>
            {PERIODS.map(p => (
              <td key={p} className="px-4 py-3.5 text-center text-sm">
                {data.viewings[p] > 0 ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                    {data.viewings[p]}
                  </span>
                ) : (
                  <span className="text-slate-400">0</span>
                )}
              </td>
            ))}
          </tr>

          {/* Contracts row */}
          <tr className="bg-slate-50">
            <td className="px-6 py-3.5 text-sm text-slate-900">
              <div className="flex items-center gap-2">
                <FileSignature className="w-4 h-4 text-green-500" />
                <span className="font-medium">Contracts Signed</span>
              </div>
            </td>
            {PERIODS.map(p => {
              const count = contracts[p]?.count || 0
              const isExpanded = expandedPeriod === p
              return (
                <td key={p} className="px-4 py-3.5 text-center text-sm">
                  {count > 0 ? (
                    <button
                      onClick={() => togglePeriod(p)}
                      className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 hover:bg-green-200 transition-colors"
                    >
                      {count}
                      {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  ) : (
                    <span className="text-slate-400">0</span>
                  )}
                </td>
              )
            })}
          </tr>
        </tbody>
      </table>

      {/* Expanded contract details */}
      {expandedPeriod && expandedContracts.length > 0 && (
        <div className="border-t border-slate-200">
          <div className="px-6 py-3 bg-green-50">
            <p className="text-xs font-medium text-green-800">
              Contracts signed in the last {PERIOD_LABELS[expandedPeriod].toLowerCase()}
            </p>
          </div>
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50">
                <th className="px-6 py-2 text-left text-xs font-medium text-slate-500 uppercase">Name</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Unit</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Signed</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Start</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">End</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-slate-500 uppercase">Rate/wk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {expandedContracts.map((c, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                  <td className="px-6 py-2.5 text-sm font-medium text-slate-900">{c.name}</td>
                  <td className="px-4 py-2.5 text-sm text-slate-700">{c.unit || '—'}</td>
                  <td className="px-4 py-2.5 text-sm text-slate-600">{formatDate(c.sign_date)}</td>
                  <td className="px-4 py-2.5 text-sm text-slate-600">{formatDate(c.start_date)}</td>
                  <td className="px-4 py-2.5 text-sm text-slate-600">{formatDate(c.end_date)}</td>
                  <td className="px-4 py-2.5 text-sm text-slate-700 text-right">
                    {c.rate ? `£${Number(c.rate).toLocaleString()}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
