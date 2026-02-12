import { useState, useMemo } from 'react'
import { ChevronDown, ChevronRight, LayoutGrid, Table } from 'lucide-react'
import RoomTimeline from './RoomTimeline'

export default function RoomsList({ rooms, loading }) {
  const [viewMode, setViewMode] = useState('timeline') // 'timeline' or 'table'
  const [expandedFloors, setExpandedFloors] = useState(new Set(['1', '2', '3', '4', '5', '6']))
  const [floorFilter, setFloorFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  // Group rooms by floor
  const roomsByFloor = useMemo(() => {
    const groups = {}
    for (const room of rooms) {
      const floor = room.floor || 'Unknown'
      if (!groups[floor]) {
        groups[floor] = []
      }
      groups[floor].push(room)
    }
    return groups
  }, [rooms])

  // Get unique floors
  const floors = useMemo(() => {
    return Object.keys(roomsByFloor).sort((a, b) => {
      const numA = parseInt(a, 10)
      const numB = parseInt(b, 10)
      if (!isNaN(numA) && !isNaN(numB)) return numA - numB
      return a.localeCompare(b)
    })
  }, [roomsByFloor])

  // Filter rooms
  const filteredRoomsByFloor = useMemo(() => {
    const result = {}
    for (const [floor, floorRooms] of Object.entries(roomsByFloor)) {
      if (floorFilter !== 'all' && floor !== floorFilter) continue

      const filtered = floorRooms.filter((room) => {
        if (statusFilter === 'all') return true
        const hasActiveContract = room.contracts?.some((c) => c.status === 'active')
        if (statusFilter === 'occupied') return hasActiveContract
        if (statusFilter === 'vacant') return !hasActiveContract
        return true
      })

      if (filtered.length > 0) {
        result[floor] = filtered
      }
    }
    return result
  }, [roomsByFloor, floorFilter, statusFilter])

  // Calculate floor stats
  const getFloorStats = (floor) => {
    const floorRooms = roomsByFloor[floor] || []
    const occupied = floorRooms.filter((room) =>
      room.contracts?.some((c) => c.status === 'active')
    ).length
    return { total: floorRooms.length, occupied }
  }

  const toggleFloor = (floor) => {
    const newExpanded = new Set(expandedFloors)
    if (newExpanded.has(floor)) {
      newExpanded.delete(floor)
    } else {
      newExpanded.add(floor)
    }
    setExpandedFloors(newExpanded)
  }

  // Generate month headers for timeline view
  const months = useMemo(() => {
    const result = []
    const today = new Date()
    const current = new Date(today.getFullYear(), today.getMonth(), 1)
    for (let i = 0; i < 12; i++) {
      result.push(current.toLocaleDateString('en-GB', { month: 'short' }))
      current.setMonth(current.getMonth() + 1)
    }
    return result
  }, [])

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-slate-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters and View Toggle */}
      <div className="flex flex-wrap items-center gap-4 justify-between">
        <div className="flex items-center gap-3">
          <select
            value={floorFilter}
            onChange={(e) => setFloorFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white"
          >
            <option value="all">All Floors</option>
            {floors.map((floor) => (
              <option key={floor} value={floor}>
                Floor {floor}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white"
          >
            <option value="all">All Status</option>
            <option value="occupied">Occupied</option>
            <option value="vacant">Vacant</option>
          </select>
        </div>

        <div className="inline-flex items-center bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('timeline')}
            className={`flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              viewMode === 'timeline'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LayoutGrid className="w-4 h-4" />
            Timeline
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              viewMode === 'table'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Table className="w-4 h-4" />
            Table
          </button>
        </div>
      </div>

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="card">
          {/* Month headers */}
          <div className="flex items-center gap-4 mb-4 pb-3 border-b border-slate-200">
            <div className="w-16 flex-shrink-0 text-xs font-medium text-slate-500">
              Room
            </div>
            <div className="w-32 flex-shrink-0 text-xs font-medium text-slate-500">
              Tenant
            </div>
            <div className="flex-1 flex">
              {months.map((month, i) => (
                <div
                  key={i}
                  className="flex-1 text-xs text-center text-slate-500"
                >
                  {month}
                </div>
              ))}
            </div>
          </div>

          {/* Floor groups */}
          {Object.entries(filteredRoomsByFloor).map(([floor, floorRooms]) => {
            const stats = getFloorStats(floor)
            const isExpanded = expandedFloors.has(floor)

            return (
              <div key={floor} className="mb-2">
                <button
                  onClick={() => toggleFloor(floor)}
                  className="w-full flex items-center gap-2 px-3 py-2 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                  <span className="font-medium text-slate-700">
                    Floor {floor}
                  </span>
                  <span className="text-sm text-slate-500">
                    — {stats.occupied}/{stats.total} occupied
                  </span>
                </button>

                {isExpanded && (
                  <div className="mt-1 pl-4">
                    {floorRooms.map((room) => (
                      <RoomTimeline key={room.room_id} room={room} />
                    ))}
                  </div>
                )}
              </div>
            )
          })}

          {/* Legend */}
          <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-3 rounded bg-blue-500"></div>
              <span className="text-slate-600">Active</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-3 rounded bg-blue-300"></div>
              <span className="text-slate-600">Future</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-3 rounded bg-slate-400"></div>
              <span className="text-slate-600">Past</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-3 rounded"
                style={{
                  backgroundImage:
                    'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(251, 191, 36, 0.4) 2px, rgba(251, 191, 36, 0.4) 4px)',
                }}
              ></div>
              <span className="text-slate-600">Vacant</span>
            </div>
          </div>
        </div>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="card overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">
                  Room
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">
                  Floor
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">
                  Current Tenant
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">
                  Start
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">
                  End
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 uppercase">
                  Next Booking
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.values(filteredRoomsByFloor)
                .flat()
                .map((room) => {
                  const activeContract = room.contracts?.find(
                    (c) => c.status === 'active'
                  )
                  const futureContract = room.contracts?.find(
                    (c) => c.status === 'future'
                  )
                  const isOccupied = !!activeContract

                  return (
                    <tr
                      key={room.room_id}
                      className="border-b border-slate-100 hover:bg-slate-50"
                    >
                      <td className="py-3 px-4 font-medium text-slate-700">
                        {room.room_id}
                      </td>
                      <td className="py-3 px-4 text-slate-600">{room.floor}</td>
                      <td className="py-3 px-4 text-slate-600">
                        {activeContract?.resident_name || '—'}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {activeContract
                          ? formatDate(activeContract.start_date)
                          : '—'}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {activeContract
                          ? formatDate(activeContract.end_date)
                          : '—'}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                            isOccupied
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-amber-100 text-amber-700'
                          }`}
                        >
                          {isOccupied ? 'Occupied' : 'Vacant'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {futureContract
                          ? `${futureContract.resident_name} (${formatDate(futureContract.start_date)})`
                          : '—'}
                      </td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })
}
