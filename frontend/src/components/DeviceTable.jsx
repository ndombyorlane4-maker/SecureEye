// src/components/DeviceTable.jsx
export default function DeviceTable({ devices }) {
  return (
    <div className='bg-black/40 border border-white/10 rounded-xl p-4 backdrop-blur-sm'>
      <h2 className='text-accent font-mono text-sm tracking-widest mb-3'>CONNECTED DEVICES</h2>
      <div className='overflow-x-auto'>
        <table className='w-full text-sm'>
          <thead>
            <tr className='text-white/40 text-xs font-mono border-b border-white/10'>
              <th className='text-left py-2 pr-4'>STATUS</th>
              <th className='text-left py-2 pr-4'>HOSTNAME</th>
              <th className='text-left py-2 pr-4'>IP ADDRESS</th>
              <th className='text-left py-2'>LAST SEEN</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d, i) => (
              <tr key={i} className='border-b border-white/5 hover:bg-white/5 transition'>
                <td className='py-2 pr-4'>
                  <span className={`inline-block w-2 h-2 rounded-full mr-2 ${d.status==='active' ? 'bg-green-400' : 'bg-red-400'}`} />
                  <span className={d.status==='active' ? 'text-green-400' : 'text-red-400'}>
                    {d.status.toUpperCase()}
                  </span>
                </td>
                <td className='py-2 pr-4 text-white font-medium'>{d.name || 'Unknown'}</td>
                <td className='py-2 pr-4 text-white/70 font-mono'>{d.ip}</td>
                <td className='py-2 text-white/40 text-xs font-mono'>{new Date().toLocaleTimeString()}</td>
              </tr>
            ))}
            {devices.length === 0 && (
              <tr><td colSpan={4} className='text-center text-white/30 py-8 font-mono text-xs'>
                No devices found — run nmap scan
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
