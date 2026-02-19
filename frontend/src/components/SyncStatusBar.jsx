import { useState, useEffect } from 'react'
import { RefreshCw, CheckCircle, AlertCircle } from 'lucide-react'
import { API_BASE } from '../config'

export default function SyncStatusBar() {
  const [syncStatus, setSyncStatus] = useState(null)
  const [syncing, setSyncing] = useState(false)
  const [loading, setLoading] = useState(true)

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/sync/status`)
      if (res.ok) {
        const data = await res.json()
        setSyncStatus(data)
        setSyncing(data.sync.status === 'syncing')
      }
    } catch (err) {
      console.error('Failed to fetch sync status:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  useEffect(() => {
    if (!syncing) return
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [syncing])

  const handleSync = async () => {
    setSyncing(true)
    try {
      await fetch(`${API_BASE}/sync/run`, { method: 'POST' })
      const poll = setInterval(async () => {
        const res = await fetch(`${API_BASE}/sync/status`)
        if (res.ok) {
          const data = await res.json()
          setSyncStatus(data)
          if (data.sync.status !== 'syncing') {
            setSyncing(false)
            clearInterval(poll)
            window.location.reload()
          }
        }
      }, 2000)
    } catch (err) {
      console.error('Sync failed:', err)
      setSyncing(false)
    }
  }

  if (loading) return null

  const lastSync = syncStatus?.sync
  const result = lastSync?.result

  return (
    <div className="flex items-center gap-3 mb-6 justify-end">
      {result && !result.error && lastSync?.status === 'completed' && (
        <div className="flex items-center gap-1 text-xs text-green-600">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Up to date</span>
        </div>
      )}

      {result?.error && (
        <div className="flex items-center gap-1 text-xs text-red-600">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Sync error</span>
        </div>
      )}

      <button
        onClick={handleSync}
        disabled={syncing}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 transition-colors"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
        {syncing ? 'Syncing...' : 'Sync Now'}
      </button>
    </div>
  )
}
