import { useState, useEffect } from 'react'
import { DoorOpen, Users, Building2 } from 'lucide-react'
import RoomsList from '../components/Rooms/RoomsList'
import StatCard from '../components/ui/StatCard'

const API_BASE = '/api'

export default function RoomsPage() {
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/occupancy/rooms/timelines`)
      if (response.ok) {
        setRooms(await response.json())
      }
    } catch (err) {
      console.error('Failed to fetch rooms:', err)
    } finally {
      setLoading(false)
    }
  }

  // Calculate summary stats
  const totalRooms = rooms.length
  const occupiedRooms = rooms.filter((room) =>
    room.contracts?.some((c) => c.status === 'active')
  ).length
  const vacantRooms = totalRooms - occupiedRooms
  const occupancyRate = totalRooms > 0 ? Math.round((occupiedRooms / totalRooms) * 100) : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Rooms</h1>
        <p className="text-slate-500 mt-1">
          View all {totalRooms} rooms and their booking timelines
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Rooms"
          value={totalRooms}
          icon={Building2}
          color="primary"
        />
        <StatCard
          title="Occupied"
          value={occupiedRooms}
          subtitle={`${occupancyRate}% occupancy`}
          icon={Users}
          color="green"
        />
        <StatCard
          title="Vacant"
          value={vacantRooms}
          subtitle="Available for booking"
          icon={DoorOpen}
          color={vacantRooms > 20 ? 'amber' : 'green'}
        />
      </div>

      {/* Rooms list with timeline */}
      <RoomsList rooms={rooms} loading={loading} />
    </div>
  )
}
