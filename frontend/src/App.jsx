import { useState, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Layout/Sidebar'
import OccupancyPage from './pages/OccupancyPage'
import CashFlowPage from './pages/CashFlowPage'
import RoomsPage from './pages/RoomsPage'
import RoomsMapPage from './pages/RoomsMapPage'
import SyncStatusBar from './components/SyncStatusBar'

export const SidebarContext = createContext()

export function useSidebar() {
  return useContext(SidebarContext)
}

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <BrowserRouter basename="/more_house">
      <SidebarContext.Provider value={{ collapsed: sidebarCollapsed, setCollapsed: setSidebarCollapsed }}>
        <div className="min-h-screen bg-slate-50">
          <Sidebar />

          {/* Main content area - offset by sidebar width */}
          <main
            className={`transition-all duration-300 ${
              sidebarCollapsed ? 'ml-16' : 'ml-56'
            }`}
          >
            <div className="max-w-7xl mx-auto px-6 py-8">
              <SyncStatusBar />
              <Routes>
                <Route path="/" element={<OccupancyPage />} />
                <Route path="/cashflow" element={<CashFlowPage />} />
                <Route path="/rooms" element={<RoomsPage />} />
                <Route path="/rooms-map" element={<RoomsMapPage />} />
              </Routes>
            </div>
          </main>
        </div>
      </SidebarContext.Provider>
    </BrowserRouter>
  )
}

export default App
