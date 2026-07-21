import React, { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { getAlerts } from '../api/dashboard'

const COLORS = ['#1B4FBF', '#E8261A', '#F59E0B', '#10B981', '#8B5CF6', '#EC4899']

function buildProtocolData(alerts) {
  const counts = {}
  alerts.forEach(a => {
    const proto = a.protocol || 'Unknown'
    counts[proto] = (counts[proto] || 0) + 1
  })
  return Object.entries(counts).map(([name, value]) => ({ name, value }))
}

export default function ProtocolChart() {
  const [data, setData] = useState([])

  useEffect(() => {
    async function load() {
      try {
        const alerts = await getAlerts()
        setData(buildProtocolData(alerts))
      } catch {}
    }
    load()
    const id = setInterval(load, 15000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="glass p-6">
      <h2 className="text-white font-semibold text-lg mb-4">🌐 Protocol Distribution</h2>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" outerRadius={80}
               dataKey="value" nameKey="name" label>
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#0D1F5C', border: '1px solid #1B4FBF',
                            borderRadius: 8, color: '#fff' }}
          />
          <Legend wrapperStyle={{ color: '#D1D5DB', fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
