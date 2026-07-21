// src/components/PacketStream.jsx
export default function PacketStream({ packets }) {

  const getProtoColor = (proto) => {
    const colors = {
      'HTTPS': 'text-green-400 bg-green-400/10 border-green-400/30',
      'HTTP':  'text-blue-400 bg-blue-400/10 border-blue-400/30',
      'DNS':   'text-orange-400 bg-orange-400/10 border-orange-400/30',
      'SSH':   'text-red-400 bg-red-400/10 border-red-400/30',
      'ICMP':  'text-purple-400 bg-purple-400/10 border-purple-400/30',
      'TCP':   'text-cyan-400 bg-cyan-400/10 border-cyan-400/30',
      'UDP':   'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
    };
    return colors[proto] || 'text-white/50 bg-white/5 border-white/10';
  };

  return (
    <div className='bg-black/40 border border-white/10 rounded-xl p-4 backdrop-blur-sm'>
      
      {/* Header */}
      <h2 className='text-accent font-mono text-sm tracking-widest mb-3'>
        📡 LIVE PACKET STREAM
      </h2>

      {/* Column Headers */}
      <div className='grid grid-cols-4 gap-2 text-white/30 
                      text-xs font-mono border-b border-white/10 
                      pb-2 mb-2'>
        <span>TIME</span>
        <span>SOURCE</span>
        <span>PROTO</span>
        <span>STATUS</span>
      </div>

      {/* Packet Rows */}
      <div className='space-y-1 max-h-64 overflow-y-auto'>
        {packets.map((pkt, i) => (
          <div
            key={i}
            className={`grid grid-cols-4 gap-2 text-xs font-mono 
                        py-1 border-b border-white/5 
                        hover:bg-white/5 transition rounded px-1
                        ${pkt.label === 'ATTACK' ? 
                          'bg-red-500/10 border-red-500/20' : ''}`}
          >
            {/* Time */}
            <span className='text-white/40'>
              {pkt.time || '--:--:--'}
            </span>

            {/* Source IP */}
            <span className='text-white/70 truncate'>
              {pkt.src || '0.0.0.0'}
            </span>

            {/* Protocol Badge */}
            <span>
              <span className={`inline-block px-1.5 py-0.5 rounded 
                               border text-xs font-bold
                               ${getProtoColor(pkt.protocol)}`}>
                {pkt.protocol || 'TCP'}
              </span>
            </span>

            {/* Status */}
            <span className={pkt.label === 'ATTACK' ? 
                            'text-red-400 font-bold' : 
                            'text-green-400'}>
              {pkt.label || 'NORMAL'}
            </span>
          </div>
        ))}

        {/* Empty state */}
        {packets.length === 0 && (
          <div className='text-center text-white/30 
                          text-xs font-mono py-8'>
            Waiting for packets...
          </div>
        )}
      </div>

      {/* Footer counter */}
      <div className='mt-3 pt-2 border-t border-white/10 
                      flex justify-between text-xs font-mono 
                      text-white/30'>
        <span>Total: {packets.length} packets</span>
        <span className='text-red-400'>
          Attacks: {packets.filter(p => p.label === 'ATTACK').length}
        </span>
      </div>
    </div>
  );
}