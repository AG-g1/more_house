const periods = [
  { value: '12m', label: '12 months', granularity: 'monthly' },
  { value: '9m', label: '9 months', granularity: 'monthly' },
  { value: '6m', label: '6 months', granularity: 'monthly' },
  { value: '3m', label: '3 months', granularity: 'weekly' },
  { value: '2m', label: '2 months', granularity: 'weekly' },
  { value: '4w', label: '4 weeks', granularity: 'weekly' },
]

export default function PeriodSelector({ value, onChange }) {
  return (
    <div className="inline-flex items-center bg-slate-100 rounded-lg p-1">
      {periods.map((period) => (
        <button
          key={period.value}
          onClick={() => onChange(period.value)}
          className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
            value === period.value
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          {period.value}
        </button>
      ))}
    </div>
  )
}

export function getPeriodConfig(periodValue) {
  const period = periods.find((p) => p.value === periodValue)
  if (!period) return { months: 12, weeks: 0, granularity: 'monthly' }

  switch (periodValue) {
    case '12m':
      return { months: 12, weeks: 0, granularity: 'monthly' }
    case '9m':
      return { months: 9, weeks: 0, granularity: 'monthly' }
    case '6m':
      return { months: 6, weeks: 0, granularity: 'monthly' }
    case '3m':
      return { months: 0, weeks: 13, granularity: 'weekly' }
    case '2m':
      return { months: 0, weeks: 9, granularity: 'weekly' }
    case '4w':
      return { months: 0, weeks: 4, granularity: 'weekly' }
    default:
      return { months: 12, weeks: 0, granularity: 'monthly' }
  }
}
