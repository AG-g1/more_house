import { useState, useEffect } from 'react'
import OccupancySummary from '../components/OccupancySummary'
import OccupancyChart from '../components/OccupancyChart'

const API_BASE = '/api'

export default function OccupancyPage() {
  const [occupancySummary, setOccupancySummary] = useState(null)
  const [weeklyData, setWeeklyData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [summaryRes, weeklyRes] = await Promise.all([
        fetch(`${API_BASE}/occupancy/summary`),
        fetch(`${API_BASE}/occupancy/weekly?end_date=2026-05-31`)
      ])

      if (summaryRes.ok) setOccupancySummary(await summaryRes.json())
      if (weeklyRes.ok) setWeeklyData(await weeklyRes.json())
    } catch (err) {
      console.error('Failed to fetch data:', err)
    } finally {
      setLoading(false)
    }
  }

  const currentOccupancy = occupancySummary?.occupied || 0

  const formatWeekRange = (startDate, endDate) => {
    const start = new Date(startDate)
    const end = new Date(endDate)
    const formatDate = (d) => d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
    return `${formatDate(start)} - ${formatDate(end)}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Monitor room occupancy and forecast</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <>
          <OccupancySummary data={occupancySummary} />
          <OccupancyChart currentOccupancy={currentOccupancy} />

          {/* Weekly Move-ins/Move-outs Table */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">Weekly Schedule</h2>
              <p className="text-sm text-slate-500">Move-ins and move-outs until May 31, 2026</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Week</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">Move-ins</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">Move-outs</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">Net</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Total Occupied</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {weeklyData.map((week, idx) => (
                    <tr key={week.week_start} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                      <td className="px-6 py-3 whitespace-nowrap text-sm text-slate-900">
                        {formatWeekRange(week.week_start, week.week_end)}
                      </td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm text-center">
                        {week.move_ins > 0 ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            +{week.move_ins}
                          </span>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm text-center">
                        {week.move_outs > 0 ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            -{week.move_outs}
                          </span>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm text-center font-medium">
                        {week.net_change > 0 ? (
                          <span className="text-green-600">+{week.net_change}</span>
                        ) : week.net_change < 0 ? (
                          <span className="text-red-600">{week.net_change}</span>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm text-right font-semibold text-slate-900">
                        {week.end_occupancy}
                        <span className="text-slate-400 font-normal"> / 120</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {weeklyData.length === 0 && (
              <div className="px-6 py-8 text-center text-slate-500">
                No weekly data available
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
