import { NavLink } from 'react-router-dom'
import { Building2, DollarSign, DoorOpen, Map, ChevronLeft, ChevronRight } from 'lucide-react'
import { useSidebar } from '../../App'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Building2 },
  { path: '/cashflow', label: 'Cash Flow', icon: DollarSign },
  { path: '/rooms', label: 'Rooms', icon: DoorOpen },
  { path: '/rooms-map', label: 'Rooms Map', icon: Map },
]

export default function Sidebar() {
  const { collapsed, setCollapsed } = useSidebar()

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-slate-900 text-white flex flex-col transition-all duration-300 z-20 ${
        collapsed ? 'w-16' : 'w-56'
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-700">
        <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <Building2 className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-lg font-semibold whitespace-nowrap">More House</h1>
            <p className="text-xs text-slate-400 whitespace-nowrap">Dashboard</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && <span className="font-medium">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center gap-2 px-4 py-3 border-t border-slate-700 text-slate-400 hover:text-white transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="w-5 h-5" />
        ) : (
          <>
            <ChevronLeft className="w-5 h-5" />
            <span className="text-sm">Collapse</span>
          </>
        )}
      </button>
    </aside>
  )
}
