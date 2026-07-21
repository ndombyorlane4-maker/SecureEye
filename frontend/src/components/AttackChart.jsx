import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { getAlerts } from '../api/dashboard'

// Group alerts by minute to build time-series data
function buildChartData(alerts) {
  const counts = {}
  alerts.forEach(a => {
    const minute = new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    counts[minute] = (counts[minute] || 0) + 1
  })
  return Object.entries(counts).slice(-20).map(([time, count]) => ({ time, count }))
}

export default function AttackChart() {
  const [data, setData] = useState([])

  useEffect(() => {
    async function load() {
      try {
        const alerts = await getAlerts()
        setData(buildChartData(alerts))
      } catch {}
    }
    load()
    const id = setInterval(load, 15000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="glass p-6">
      <h2 className="text-white font-semibold text-lg mb-4">⚡ Attack Count Over Time</h2>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey="time" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
          <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: '#0D1F5C', border: '1px solid #1B4FBF',
                            borderRadius: 8, color: '#fff' }}
          />
          <Line type="monotone" dataKey="count" stroke="#E8261A"
                strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
} // L'accolade ferme proprement la fonction ici, et il n'y a plus de double export parasite.
