import React, { useEffect, useState } from 'react'
import { getPreventionStatus, setPrevention } from '../api/dashboard'

export default function PreventionPanel() {
  const [enabled,  setEnabled]  = useState(false)
  const [loading,  setLoading]  = useState(true)
  const [saving,   setSaving]   = useState(false)
  const [message,  setMessage]  = useState('')

  useEffect(() => {
    async function load() {
      try {
        const data = await getPreventionStatus()
        setEnabled(data.enabled)
      } catch {} finally { setLoading(false) }
    }
    load()
  }, [])

  async function toggle() {
    setSaving(true)
    setMessage('')
    try {
      await setPrevention(!enabled)
      setEnabled(!enabled)
      setMessage(enabled ? 'Prevention mode disabled.' : 'Prevention mode enabled.')
    } catch {
      setMessage('Error updating prevention mode.')
    } finally { setSaving(false) }
  }

  return (
    <div className="glass p-6 max-w-xl">
      <h2 className="text-white font-semibold text-lg mb-6">⚙️ Prevention Mode</h2>

      {loading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : (
        <div className="space-y-6">

          {/* Status indicator */}
          <div className="flex items-center gap-4 p-5 rounded-xl bg-white/5 border border-white/10">
            <span className={`w-5 h-5 rounded-full ${enabled ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
            <div>
              <div className="text-white font-medium">
                Prevention is currently <span className={enabled ? 'text-green-400' : 'text-gray-400'}>
                  {enabled ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>
              <div className="text-gray-400 text-sm mt-0.5">
                {enabled
                  ? 'Detected attacks are being blocked automatically via iptables.'
                  : 'Detection only — no automatic blocking is applied.'}
              </div>
            </div>
          </div>

          {/* Toggle button */}
          <button
            onClick={toggle}
            disabled={saving}
            className={`w-full py-3 rounded-xl font-semibold text-white transition-all
                        ${enabled
                          ? 'bg-red-700 hover:bg-red-600'
                          : 'bg-green-700 hover:bg-green-600'}
                        disabled:opacity-50`}
          >
            {saving ? 'Updating...' : enabled ? 'Disable Prevention' : 'Enable Prevention'}
          </button>

          {/* Feedback message */}
          {message && (
            <p className="text-center text-sm text-blue-300">{message}</p>
          )}

          {/* Warning */}
          <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-xl p-4 text-sm text-yellow-300">
            ⚠️  Enabling prevention mode will automatically block IPs that trigger
            the ML detection model above the confidence threshold.
            Make sure your whitelist is up to date before enabling.
          </div>
        </div>
      )}
    </div>
  )
}