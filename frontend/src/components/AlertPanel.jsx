AlertPanel.jsx
// src/components/AlertPanel.jsx
export default function AlertPanel({ alerts }) {
  return (
    <div className='bg-black/40 border border-red-500/30 rounded-xl p-4 backdrop-blur-sm'>
      <h2 className='text-red-400 font-mono text-sm tracking-widest mb-3'>
        ⚠ SECURITY ALERTS ({alerts.length})
      </h2>
      <div className='space-y-2 max-h-64 overflow-y-auto'>
        {alerts.map((a, i) => (
          <div key={i} className='bg-red-500/10 border border-red-500/20 rounded-lg p-3'>
            <div className='flex justify-between'>
              <span className='text-red-400 font-bold text-xs font-mono'>{a.label}</span>
              <span className='text-white/30 text-xs font-mono'>{a.time}</span>
            </div>
            <p className='text-white/70 text-xs mt-1 font-mono'>
              {a.src} → {a.dst} | {a.protocol} | {a.confidence}% confidence
            </p>
          </div>
        ))}
        {alerts.length === 0 && (
          <p className='text-white/30 text-xs font-mono text-center py-8'>No alerts — network is clean</p>
        )}
      </div>
    </div>
  );
}
