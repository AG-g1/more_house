import { useState, useEffect } from 'react'
import { Building2, TrendingUp, Calendar, DollarSign, AlertTriangle, Users } from 'lucide-react'
import OccupancySummary from './components/OccupancySummary'
import OccupancyChart from './components/OccupancyChart'
import UpcomingVacancies from './components/UpcomingVacancies'
import CashFlowChart from './components/CashFlowChart'

const API_BASE = '/api'

function App() {
  const [activeTab, setActiveTab] = useState('occupancy')
  const [occupancySummary, setOccupancySummary] = useState(null)
  const [monthlyOccupancy, setMonthlyOccupancy] = useState([])
  const [upcomingVacancies, setUpcomingVacancies] = useState([])
  const [monthlyCashflow, setMonthlyCashflow] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [summaryRes, monthlyRes, vacanciesRes, cashflowRes] = await Promise.all([
        fetch(`${API_BASE}/occupancy/summary`),
        fetch(`${API_BASE}/occupancy/monthly`),
        fetch(`${API_BASE}/occupancy/vacancies/upcoming?days=60`),
        fetch(`${API_BASE}/cashflow/monthly`)
      ])

      if (summaryRes.ok) setOccupancySummary(await summaryRes.json())
      if (monthlyRes.ok) setMonthlyOccupancy(await monthlyRes.json())
      if (vacanciesRes.ok) setUpcomingVacancies(await vacanciesRes.json())
      if (cashflowRes.ok) setMonthlyCashflow(await cashflowRes.json())

    } catch (err) {
      setError('Failed to fetch data. Is the backend running?')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'occupancy', label: 'Occupancy', icon: Building2 },
    { id: 'cashflow', label: 'Cash Flow', icon: DollarSign },
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-900">More House</h1>
                <p className="text-xs text-slate-500">Occupancy & Cash Flow Dashboard</p>
              </div>
            </div>

            <nav className="flex gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <p className="text-amber-800">{error}</p>
            <button onClick={fetchData} className="ml-auto btn-secondary text-sm">
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <>
            {activeTab === 'occupancy' && (
              <div className="space-y-6">
                {/* Summary Cards */}
                <OccupancySummary data={occupancySummary} />

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <OccupancyChart data={monthlyOccupancy} />
                  <UpcomingVacancies data={upcomingVacancies} />
                </div>
              </div>
            )}

            {activeTab === 'cashflow' && (
              <div className="space-y-6">
                <CashFlowChart data={monthlyCashflow} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
