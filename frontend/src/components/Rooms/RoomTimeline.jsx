import { useMemo } from 'react'

const MONTHS_TO_SHOW = 12

export default function RoomTimeline({ room, startDate }) {
  const today = startDate || new Date()

  // Generate month labels
  const months = useMemo(() => {
    const result = []
    const current = new Date(today.getFullYear(), today.getMonth(), 1)
    for (let i = 0; i < MONTHS_TO_SHOW; i++) {
      result.push({
        date: new Date(current),
        label: current.toLocaleDateString('en-GB', { month: 'short' }),
        year: current.getFullYear(),
      })
      current.setMonth(current.getMonth() + 1)
    }
    return result
  }, [today])

  // Calculate the timeline range
  const timelineStart = new Date(today.getFullYear(), today.getMonth(), 1)
  const timelineEnd = new Date(timelineStart)
  timelineEnd.setMonth(timelineEnd.getMonth() + MONTHS_TO_SHOW)
  const totalDays = Math.floor((timelineEnd - timelineStart) / (1000 * 60 * 60 * 24))

  // Calculate position and width for each contract
  const contractBars = useMemo(() => {
    if (!room.contracts || room.contracts.length === 0) return []

    return room.contracts.map((contract) => {
      const contractStart = new Date(contract.start_date)
      const contractEnd = new Date(contract.end_date)

      // Clamp to visible range
      const visibleStart = contractStart < timelineStart ? timelineStart : contractStart
      const visibleEnd = contractEnd > timelineEnd ? timelineEnd : contractEnd

      // Skip if entirely outside visible range
      if (visibleEnd <= timelineStart || visibleStart >= timelineEnd) {
        return null
      }

      const startOffset = Math.floor((visibleStart - timelineStart) / (1000 * 60 * 60 * 24))
      const endOffset = Math.floor((visibleEnd - timelineStart) / (1000 * 60 * 60 * 24))
      const width = endOffset - startOffset

      const left = (startOffset / totalDays) * 100
      const widthPercent = (width / totalDays) * 100

      // Determine color based on status
      let bgColor = 'bg-blue-500' // active
      if (contract.status === 'future') {
        bgColor = 'bg-blue-300'
      } else if (contract.status === 'past') {
        bgColor = 'bg-slate-400'
      }

      return {
        ...contract,
        left,
        width: widthPercent,
        bgColor,
      }
    }).filter(Boolean)
  }, [room.contracts, timelineStart, timelineEnd, totalDays])

  // Find gaps (vacant periods)
  const gaps = useMemo(() => {
    if (!room.contracts || room.contracts.length === 0) {
      // Entire timeline is vacant
      return [{ left: 0, width: 100 }]
    }

    const sortedContracts = [...room.contracts]
      .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))

    const result = []
    let lastEnd = timelineStart

    for (const contract of sortedContracts) {
      const contractStart = new Date(contract.start_date)
      const contractEnd = new Date(contract.end_date)

      // Check for gap before this contract
      if (contractStart > lastEnd && contractStart < timelineEnd && lastEnd >= timelineStart) {
        const gapStart = lastEnd < timelineStart ? timelineStart : lastEnd
        const gapEnd = contractStart > timelineEnd ? timelineEnd : contractStart

        const startOffset = Math.floor((gapStart - timelineStart) / (1000 * 60 * 60 * 24))
        const endOffset = Math.floor((gapEnd - timelineStart) / (1000 * 60 * 60 * 24))
        const width = endOffset - startOffset

        if (width > 0) {
          result.push({
            left: (startOffset / totalDays) * 100,
            width: (width / totalDays) * 100,
          })
        }
      }

      if (contractEnd > lastEnd) {
        lastEnd = contractEnd
      }
    }

    // Check for gap after last contract
    if (lastEnd < timelineEnd) {
      const gapStart = lastEnd < timelineStart ? timelineStart : lastEnd
      const startOffset = Math.floor((gapStart - timelineStart) / (1000 * 60 * 60 * 24))
      const width = totalDays - startOffset

      if (width > 0) {
        result.push({
          left: (startOffset / totalDays) * 100,
          width: (width / totalDays) * 100,
        })
      }
    }

    return result
  }, [room.contracts, timelineStart, timelineEnd, totalDays])

  // Get current tenant
  const currentContract = room.contracts?.find((c) => c.status === 'active')
  const currentTenant = currentContract?.resident_name || '—'

  return (
    <div className="flex items-center gap-4 py-2 border-b border-slate-100 last:border-0">
      {/* Room info */}
      <div className="w-16 flex-shrink-0">
        <span className="font-medium text-slate-700">{room.room_id}</span>
      </div>
      <div className="w-32 flex-shrink-0 truncate">
        <span className="text-sm text-slate-600">{currentTenant}</span>
      </div>

      {/* Timeline bar */}
      <div className="flex-1 relative h-6 bg-slate-100 rounded overflow-hidden">
        {/* Month grid lines */}
        {months.slice(1).map((month, i) => (
          <div
            key={i}
            className="absolute top-0 bottom-0 w-px bg-slate-200"
            style={{ left: `${((i + 1) / MONTHS_TO_SHOW) * 100}%` }}
          />
        ))}

        {/* Vacant gaps (amber striped) */}
        {gaps.map((gap, i) => (
          <div
            key={`gap-${i}`}
            className="absolute top-0 bottom-0"
            style={{
              left: `${gap.left}%`,
              width: `${gap.width}%`,
              backgroundImage:
                'repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(251, 191, 36, 0.3) 4px, rgba(251, 191, 36, 0.3) 8px)',
            }}
          />
        ))}

        {/* Contract bars */}
        {contractBars.map((bar, i) => (
          <div
            key={i}
            className={`absolute top-1 bottom-1 ${bar.bgColor} rounded-sm`}
            style={{
              left: `${bar.left}%`,
              width: `${Math.max(bar.width, 0.5)}%`,
            }}
            title={`${bar.resident_name}: ${bar.start_date} to ${bar.end_date}`}
          />
        ))}

        {/* Today marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
          style={{ left: '0%' }}
        />
      </div>
    </div>
  )
}
