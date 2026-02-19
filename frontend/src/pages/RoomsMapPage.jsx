import { useState, useEffect } from 'react'
import { Building2, User, Calendar, Maximize2 } from 'lucide-react'
import { API_BASE } from '../config'

// Floor order from top to bottom of building
const FLOOR_ORDER = ['Fifth', 'Fourth', 'Third', 'Second', 'First', 'Mezz', 'G', 'LG']

// Floor display names
const FLOOR_NAMES = {
  'Fifth': '5th Floor',
  'Fourth': '4th Floor',
  'Third': '3rd Floor',
  'Second': '2nd Floor',
  'First': '1st Floor',
  'Mezz': 'Mezzanine',
  'G': 'Ground',
  'LG': 'Lower Ground'
}

// Category colors
const CATEGORY_COLORS = {
  'Superior Mezzanine': 'bg-purple-500',
  'Deluxe Mezzanine': 'bg-indigo-500',
  'Deluxe': 'bg-blue-500',
  'Bespoke': 'bg-cyan-500',
  'Classic': 'bg-emerald-500',
  'Standard': 'bg-slate-400',
}

function RoomCard({ room, onClick }) {
  const isOccupied = room.status === 'Occupied'
  const categoryColor = CATEGORY_COLORS[room.category] || 'bg-slate-400'

  return (
    <div
      onClick={() => onClick(room)}
      className={`
        relative p-2 rounded-lg cursor-pointer transition-all duration-200
        border-2 hover:scale-105 hover:shadow-lg hover:z-10
        ${isOccupied
          ? 'bg-white border-slate-200 hover:border-primary-400'
          : 'bg-slate-100 border-dashed border-slate-300 hover:border-amber-400'
        }
      `}
      style={{ minWidth: '80px' }}
    >
      {/* Category indicator */}
      <div className={`absolute top-0 left-0 right-0 h-1 rounded-t-md ${categoryColor}`} />

      {/* Room number */}
      <div className="text-sm font-bold text-slate-800 mt-1">
        {room.room_id}
      </div>

      {/* Status indicator */}
      <div className="flex items-center gap-1 mt-1">
        {isOccupied ? (
          <>
            <User className="w-3 h-3 text-primary-600" />
            <span className="text-xs text-slate-600 truncate max-w-[60px]">
              {room.current_tenant?.split(' ')[0] || 'Occupied'}
            </span>
          </>
        ) : (
          <span className="text-xs text-amber-600 font-medium">Vacant</span>
        )}
      </div>

      {/* Size */}
      {room.sqm && (
        <div className="text-xs text-slate-400 mt-0.5">
          {room.sqm}m²
        </div>
      )}
    </div>
  )
}

function FloorRow({ floor, rooms, onRoomClick }) {
  // Sort rooms by room number
  const sortedRooms = [...rooms].sort((a, b) => {
    const aNum = parseFloat(a.room_id.replace(/[^\d.-]/g, '')) || 0
    const bNum = parseFloat(b.room_id.replace(/[^\d.-]/g, '')) || 0
    return aNum - bNum
  })

  const occupiedCount = rooms.filter(r => r.status === 'Occupied').length
  const totalRooms = rooms.length

  return (
    <div className="flex items-stretch border-b border-slate-200 last:border-b-0">
      {/* Floor label */}
      <div className="w-32 flex-shrink-0 bg-slate-800 text-white p-3 flex flex-col justify-center">
        <div className="font-semibold text-sm">{FLOOR_NAMES[floor] || floor}</div>
        <div className="text-xs text-slate-300 mt-1">
          {occupiedCount}/{totalRooms} occupied
        </div>
        <div className="w-full bg-slate-600 rounded-full h-1.5 mt-2">
          <div
            className="bg-primary-400 h-1.5 rounded-full transition-all"
            style={{ width: `${(occupiedCount / totalRooms) * 100}%` }}
          />
        </div>
      </div>

      {/* Rooms */}
      <div className="flex-1 p-3 bg-slate-50 flex flex-wrap gap-2 items-start">
        {sortedRooms.map(room => (
          <RoomCard key={room.room_id} room={room} onClick={onRoomClick} />
        ))}
      </div>
    </div>
  )
}

function RoomDetailModal({ room, onClose }) {
  if (!room) return null

  const isOccupied = room.status === 'Occupied'
  const categoryColor = CATEGORY_COLORS[room.category] || 'bg-slate-400'

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`${categoryColor} text-white p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Room {room.room_id}</h2>
              <p className="text-white/80">{room.category}</p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              isOccupied ? 'bg-white/20' : 'bg-amber-400 text-amber-900'
            }`}>
              {isOccupied ? 'Occupied' : 'Vacant'}
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="text-xs text-slate-500 uppercase tracking-wide">Floor</div>
              <div className="text-lg font-semibold text-slate-800">
                {FLOOR_NAMES[room.floor] || room.floor}
              </div>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="text-xs text-slate-500 uppercase tracking-wide">Size</div>
              <div className="text-lg font-semibold text-slate-800">
                {room.sqm ? `${room.sqm} m²` : 'N/A'}
              </div>
            </div>
          </div>

          {isOccupied && (
            <div className="bg-primary-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-primary-800 mb-2">
                <User className="w-4 h-4" />
                <span className="font-medium">Current Tenant</span>
              </div>
              <div className="text-slate-800 font-semibold">{room.current_tenant}</div>
              {room.start_date && room.end_date && (
                <div className="flex items-center gap-2 mt-2 text-sm text-slate-600">
                  <Calendar className="w-4 h-4" />
                  <span>{room.start_date} to {room.end_date}</span>
                </div>
              )}
            </div>
          )}

          {!isOccupied && (
            <div className="bg-amber-50 rounded-lg p-4 text-center">
              <div className="text-amber-800 font-medium">This room is available</div>
              <div className="text-sm text-amber-600 mt-1">Ready for new booking</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t p-4">
          <button
            onClick={onClose}
            className="w-full py-2 px-4 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-700 font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function Legend() {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-4">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">Room Categories</h3>
      <div className="flex flex-wrap gap-3">
        {Object.entries(CATEGORY_COLORS).map(([category, color]) => (
          <div key={category} className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded ${color}`} />
            <span className="text-xs text-slate-600">{category}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-3 pt-3 border-t">
        <div className="flex items-center gap-2">
          <div className="w-6 h-4 bg-white border-2 border-slate-200 rounded" />
          <span className="text-xs text-slate-600">Occupied</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-4 bg-slate-100 border-2 border-dashed border-slate-300 rounded" />
          <span className="text-xs text-slate-600">Vacant</span>
        </div>
      </div>
    </div>
  )
}

export default function RoomsMapPage() {
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedRoom, setSelectedRoom] = useState(null)

  useEffect(() => {
    fetchRooms()
  }, [])

  const fetchRooms = async () => {
    try {
      const response = await fetch(`${API_BASE}/occupancy/rooms`)
      if (!response.ok) throw new Error('Failed to fetch rooms')
      const data = await response.json()
      // Filter out placeholder rooms (those with TBD floor or not in the building)
      const validRooms = data.filter(room =>
        room.floor && room.floor !== 'TBD' && FLOOR_ORDER.includes(room.floor)
      )
      setRooms(validRooms)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Group rooms by floor
  const roomsByFloor = rooms.reduce((acc, room) => {
    const floor = room.floor || 'Unknown'
    if (!acc[floor]) acc[floor] = []
    acc[floor].push(room)
    return acc
  }, {})

  // Calculate stats
  const totalRooms = rooms.length
  const occupiedRooms = rooms.filter(r => r.status === 'Occupied').length
  const vacantRooms = totalRooms - occupiedRooms
  const occupancyRate = totalRooms > 0 ? ((occupiedRooms / totalRooms) * 100).toFixed(1) : 0

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-lg">
        Error loading rooms: {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
            <Building2 className="w-7 h-7 text-primary-600" />
            Rooms Map
          </h1>
          <p className="text-slate-500 mt-1">Building overview with all {totalRooms} rooms</p>
        </div>

        {/* Quick stats */}
        <div className="flex gap-4">
          <div className="bg-primary-50 px-4 py-2 rounded-lg">
            <div className="text-2xl font-bold text-primary-700">{occupiedRooms}</div>
            <div className="text-xs text-primary-600">Occupied</div>
          </div>
          <div className="bg-amber-50 px-4 py-2 rounded-lg">
            <div className="text-2xl font-bold text-amber-700">{vacantRooms}</div>
            <div className="text-xs text-amber-600">Vacant</div>
          </div>
          <div className="bg-slate-100 px-4 py-2 rounded-lg">
            <div className="text-2xl font-bold text-slate-700">{occupancyRate}%</div>
            <div className="text-xs text-slate-500">Occupancy</div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <Legend />

      {/* Building visualization */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {/* Roof decoration */}
        <div className="h-4 bg-gradient-to-b from-slate-700 to-slate-800" />

        {/* Floors */}
        {FLOOR_ORDER.map(floor => (
          roomsByFloor[floor] && (
            <FloorRow
              key={floor}
              floor={floor}
              rooms={roomsByFloor[floor]}
              onRoomClick={setSelectedRoom}
            />
          )
        ))}

        {/* Foundation */}
        <div className="h-6 bg-gradient-to-t from-slate-600 to-slate-700" />
      </div>

      {/* Room detail modal */}
      <RoomDetailModal
        room={selectedRoom}
        onClose={() => setSelectedRoom(null)}
      />
    </div>
  )
}
