import React from 'react'
import { logout } from '../api/auth'

const MENU = [
  { key: 'overview',   icon: '🏠', label: 'Overview'   },
  { key: 'alerts',     icon: '🚨', label: 'Alerts'     },
  { key: 'blocked',    icon: '🛡️',  label: 'Blocked IPs'},
  { key: 'machines',   icon: '💻', label: 'Machines'   },
  { key: 'prevention', icon: '⚙️',  label: 'Prevention' },
]

export default function Sidebar({ active, onSelect }) {
  return (
    <aside className="glass w-64 min-h-screen flex flex-col p-5 mr-2 rounded-none
                      border-r border-white/10" style={{ borderRadius: 0 }}>

      {/* Brand */}
      <div className="flex items-center gap-3 mb-10 px-2">
        <span className="text-3xl">👁️</span>
        <div>
          <div className="text-white font-bold text-lg leading-tight">SECURE-EYE</div>
          <div className="text-blue-400 text-xs">IDPS Dashboard</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {MENU.map(item => (
          <button
            key={item.key}
            onClick={() => onSelect(item.key)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm
                        font-medium transition-all text-left
                        ${active === item.key
                          ? 'bg-blue-600/70 text-white shadow-lg'
                          : 'text-gray-300 hover:bg-white/10 hover:text-white'}`}
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Logout */}
      <button
        onClick={logout}
        className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm
                   text-red-400 hover:bg-red-900/30 hover:text-red-300 transition-all"
      >
        <span className="text-lg">🚪</span> Logout
      </button>
    </aside>
  )
}
