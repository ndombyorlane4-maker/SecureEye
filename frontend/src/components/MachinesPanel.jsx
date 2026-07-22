import React, { useEffect, useState } from 'react'
import { getMachines } from '../api/dashboard'

const STATUS_STYLE = {
  online:  'bg-green-500',
  offline: 'bg-gray-500',
  alert:   'bg-red-500 animate-pulse',
}

export default function MachinesPanel() {
  const [machines, setMachines] = useState([])
  const [loading,  setLoading]  = useState(true)

  useEffect(() => {
    async function load() {
      try { setMachines(await getMachines()) }
      catch {} finally { setLoading(false) }
    }
    load()
    const id = setInterval(load, 15000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="glass p-6">
      <h2 className="text-white font-semibold text-lg mb-4">💻 Monitored Machines</h2>
      {loading && <p className="text-gray-400 text-sm">Loading...</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.isArray(machines) && machines.map((m, i) => (
          <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className={`w-3 h-3 rounded-full shrink-0
                               ${STATUS_STYLE[m.status] || STATUS_STYLE.offline}`} />
              <span className="text-white font-medium">{m.hostname || m.ip}</span>
              <span className="text-xs text-gray-400 ml-auto capitalize">{m.status}</span>
            </div>
            <div className="text-gray-400 text-xs space-y-1">
              <div>IP: <span className="text-gray-200 font-mono">{m.ip}</span></div>
              {m.os     && <div>OS: <span className="text-gray-200">{m.os}</span></div>}
              {m.alerts !== undefined &&
                <div>Alerts: <span className="text-red-400 font-medium">{m.alerts}</span></div>}
            </div>
          </div>
        ))}
        {!loading && machines.length === 0 && (
          <p className="text-gray-400 text-sm col-span-2">No machines detected yet.</p>
        )}
      </div>
    </div>
  )
}