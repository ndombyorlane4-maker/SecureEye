import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'


// Group alerts by minute to build time-series data safely
function buildChartData(alerts) {
  if (!Array.isArray(alerts)) return [];
  const counts = {}
  alerts.forEach(a => {
    if (a && a.timestamp) {
      const minute = new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      counts[minute] = (counts[minute] || 0) + 1
    }
  });
  return Object.entries(counts).slice(-20).map(([time, count]) => ({ time, count }))
}

export default function TrafficChart({ packets }) {
  const [data, setData] = useState([])

  // Build chart data whenever new packets or alerts arrive via props
  useEffect(() => {
    if (Array.isArray(packets)) {
      setData(buildChartData(packets))
    }
  }, [packets])

  return (
    <div className="glass rounded-xl p-4 h-64 w-full">
      <h3 className="text-white/70 text-xs font-mono mb-4 uppercase tracking-wider">Network Traffic Flow</h3>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey="time" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
          <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: '#0D1F5C', border: '1px solid #1B4FBF',
                            borderRadius: 8, color: '#fff' }}
          />
          <Line type="monotone" dataKey="count" stroke="#3B82F6"
                strokeWidth={2} dot={false} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
