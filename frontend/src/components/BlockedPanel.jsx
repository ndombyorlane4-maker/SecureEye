import React, { useEffect, useState } from 'react'
import { getBlocked, unblockIP, blockIP } from '../api/dashboard'

export default function BlockedPanel() {
  const [blocked, setBlocked] = useState([])
  const [newIP,   setNewIP]   = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    try { setBlocked(await getBlocked()) }
    catch {} finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function handleUnblock(ip) {
    try { await unblockIP(ip); await load() } catch {}
  }

  async function handleBlock() {
    if (!newIP.trim()) return
    try { await blockIP(newIP.trim()); setNewIP(''); await load() } catch {}
  }

  return (
    <div className="glass p-6">
      <h2 className="text-white font-semibold text-lg mb-4">🛡️ Blocked IP Addresses</h2>

      {/* Manual block input */}
      <div className="flex gap-3 mb-6">
        <input
          value={newIP}
          onChange={e => setNewIP(e.target.value)}
          placeholder="e.g. 192.168.1.100"
          className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-2
                     text-white text-sm placeholder-gray-500 focus:outline-none
                     focus:border-blue-400 transition"
        />
        <button onClick={handleBlock}
                className="bg-red-600 hover:bg-red-500 text-white text-sm font-medium
                           px-5 py-2 rounded-lg transition">
          Block IP
        </button>
      </div>

      {loading && <p className="text-gray-400 text-sm">Loading...</p>}
      {!loading && blocked.length === 0 && (
        <p className="text-gray-400 text-sm">No IPs currently blocked.</p>
      )}

      <div className="space-y-2 max-h-96 overflow-auto">
        {Array.isArray(blocked) && blocked.map((item, i) => (
          <div key={i} className="flex items-center justify-between
                                  bg-red-900/20 border border-red-800/40
                                  rounded-lg px-4 py-3">
            <div>
              <span className="text-white font-mono text-sm">{item.ip}</span>
              {item.reason && (
                <span className="text-gray-400 text-xs ml-3">{item.reason}</span>
              )}
            </div>
            <button onClick={() => handleUnblock(item.ip)}
                    className="text-xs text-green-400 hover:text-green-300
                               border border-green-700 hover:border-green-500
                               px-3 py-1 rounded transition">
              Unblock
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}