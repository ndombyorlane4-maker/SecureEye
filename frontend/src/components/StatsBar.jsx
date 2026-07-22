
import React, { useEffect, useState } from 'react'
import { getStats } from '../api/dashboard'

const STAT_CARDS = [
  { key: 'total_packets',   label: 'Packets Analysed', icon: '📦', color: 'text-blue-300'  },
  { key: 'attacks_detected',label: 'Attacks Detected',  icon: '🚨', color: 'text-red-400'   },
  { key: 'ips_blocked',     label: 'IPs Blocked',       icon: '🛡️',  color: 'text-yellow-300'},
  { key: 'machines_online', label: 'Machines Online',   icon: '💻', color: 'text-green-400' },
]

export default function StatsBar() {
  const [stats, setStats] = useState({})

  useEffect(() => {
    async function load() {
      try { setStats(await getStats()) } catch {}
    }
    load()
    const id = setInterval(load, 10000)   // refresh every 10 seconds
    return () => clearInterval(id)
  }, [])

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {STAT_CARDS.map(card => (
        <div key={card.key} className="glass p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{card.icon}</span>
            <span className={`text-xs font-semibold uppercase tracking-wider ${card.color}`}>
              Live
            </span>
          </div>
          <div className={`text-3xl font-bold text-white mb-1`}>
            {stats[card.key] ?? '—'}
          </div>
          <div className="text-gray-400 text-sm">{card.label}</div>
        </div>
      ))}
    </div>
  )
}
