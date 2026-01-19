import { AlertTriangle, Clock, DoorOpen } from 'lucide-react'
import { format, parseISO, differenceInDays } from 'date-fns'

function VacancyRow({ vacancy }) {
  const daysUntil = vacancy.days_until_vacant
  const urgencyColor = daysUntil <= 7 ? 'text-red-600 bg-red-50' :
                       daysUntil <= 14 ? 'text-amber-600 bg-amber-50' :
                       'text-slate-600 bg-slate-50'

  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
          <DoorOpen className="w-5 h-5 text-slate-500" />
        </div>
        <div>
          <p className="font-medium text-slate-900">Room {vacancy.room_id}</p>
          <p className="text-sm text-slate-500">{vacancy.current_tenant}</p>
        </div>
      </div>
      <div className="text-right">
        <p className="text-sm font-medium text-slate-900">
          {format(parseISO(vacancy.vacates_on), 'MMM d, yyyy')}
        </p>
        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${urgencyColor}`}>
          <Clock className="w-3 h-3" />
          {daysUntil} days
        </span>
      </div>
    </div>
  )
}

export default function UpcomingVacancies({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          <h3 className="text-lg font-semibold text-slate-900">Upcoming Vacancies</h3>
        </div>
        <div className="h-64 flex flex-col items-center justify-center text-slate-500">
          <DoorOpen className="w-12 h-12 text-slate-300 mb-3" />
          <p>No upcoming vacancies without follow-on bookings</p>
          <p className="text-sm text-slate-400 mt-1">Great job, sales team!</p>
        </div>
      </div>
    )
  }

  const urgentCount = data.filter(v => v.days_until_vacant <= 14).length

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          <h3 className="text-lg font-semibold text-slate-900">Upcoming Vacancies</h3>
        </div>
        {urgentCount > 0 && (
          <span className="text-xs font-medium px-2 py-1 rounded-full bg-red-100 text-red-700">
            {urgentCount} urgent
          </span>
        )}
      </div>

      <div className="text-sm text-slate-500 mb-4">
        Rooms becoming vacant with no follow-on booking
      </div>

      <div className="max-h-64 overflow-y-auto">
        {data.map((vacancy, idx) => (
          <VacancyRow key={idx} vacancy={vacancy} />
        ))}
      </div>

      {data.length > 5 && (
        <div className="mt-4 pt-4 border-t border-slate-100 text-center">
          <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
            View all {data.length} vacancies
          </button>
        </div>
      )}
    </div>
  )
}
