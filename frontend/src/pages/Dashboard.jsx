import { useEffect, useState, useRef } from 'react';
import { getDevices } from '../api/client';
import DeviceTable  from '../components/DeviceTable';
import AlertPanel   from '../components/AlertPanel';
import TrafficChart from '../components/TrafficChart';
import PacketStream from '../components/PacketStream';
import SideBar      from '../components/SideBar';
import StatsBar     from '../components/StatsBar';
import AttackChart  from '../components/AttackChart';
import ProtocolChart from '../components/ProtocolChart';
import BlockedPanel from '../components/BlockedPanel';
import MachinesPanel from '../components/MachinesPanel';

// Remplacez la construction de votre WS_URL par cette version plus robuste :
const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Supprime le slash final s'il existe pour éviter le double slash (//ws)
const cleanUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;

// Force 'wss' si on est sur Render (.onrender.com), sinon utilise 'ws' en local
const protocol = cleanUrl.includes('onrender.com') ? 'wss' : cleanUrl.startsWith('https') ? 'wss' : 'ws';

// Remplace http/https par ws/wss de manière propre
const WS_URL = cleanUrl.replace(/^https?/, protocol) + '/ws';

export default function Dashboard() {
  const [devices, setDevices] = useState([]);
  const [alerts,  setAlerts]  = useState([]);
  const [packets, setPackets] = useState([]);
  console.log('Packets:', packets);  // Ajoute ce log
  const wsRef = useRef(null);

  // Fetch devices every 30s
  useEffect(() => {
    const load = () => getDevices().then(r => setDevices(r.data.devices));
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  function connectWS() {
  const ws = new WebSocket('wss://secure-eye-backend.onrender.com/ws');

  ws.onclose = () => {
    console.log('WebSocket disconnected. Reconnecting in 3 seconds...');
    setTimeout(connectWS, 3000); // Retry connection
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    ws.close();
  };
}


  // WebSocket for real-time events
  useEffect(() => {
    wsRef.current = new WebSocket(WS_URL);
    wsRef.current.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'ALERT') {
        setAlerts(prev => [{ ...msg, time: new Date().toLocaleTimeString() }, ...prev].slice(0,50));
      }
      setPackets(prev => [{ ...msg, time: new Date().toLocaleTimeString() }, ...prev].slice(0,100));
    };
    return () => wsRef.current?.close();
  }, []);

  return (
    /* Structure Flexbox pour caler la SideBar à gauche sans casser votre mise en page */
    <div className='flex min-h-screen'>
      
      {/* 1. INTÉGRATION DE LA SIDEBAR MANQUANTE */}
      <SideBar />

      {/* Conteneur de votre code d'origine (prend tout l'espace restant à droite) */}
      <div className='flex-1 p-6 bg-transparent'>
        
        {/* Header (Strictement identique à votre code) */}
        <header className='flex items-center justify-between mb-6'>
          <div className='flex items-center gap-3'>
            <img src='secure-eye/frontend/public/secureeye logo.jpeg' className='h-10' alt='logo' />
            <h1 className='text-white text-2xl font-black tracking-widest'>SECURE-EYE</h1>
          </div>
          <div className='flex gap-4 text-sm font-mono text-white/60'>
            <span>🟢 LIVE</span>
            <span>{devices.length} DEVICES</span>
            <span>{alerts.length} ALERTS</span>
            <button onClick={() => { localStorage.clear(); window.location='/'; }}
                    className='text-red-400 hover:text-red-300'>Logout</button>
          </div>
        </header>

        {/* 2. INTÉGRATION DE LA STATSBAR MANQUANTE */}
        <div className='mb-6'>
          <StatsBar devices={devices} alerts={alerts} />
        </div>

        {/* Stats Row (Strictement identique à votre code) */}
        <div className='grid grid-cols-4 gap-4 mb-6'>
          {[
            { label:'Active Devices', value: devices.filter(d=>d.status==='active').length, color:'text-green-400'},
            { label:'Offline',        value: devices.filter(d=>d.status!=='active').length, color:'text-red-400'},
            { label:'Attacks Today',  value: alerts.length,                                  color:'text-orange-400'},
            { label:'Total Devices',  value: devices.length,                                 color:'text-blue-400'},
          ].map(s => (
            <div key={s.label} className='glass rounded-xl p-4 text-center'>
              <div className={`text-3xl font-black ${s.color}`}>{s.value}</div>
              <div className='text-white/50 text-xs mt-1 font-mono'>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Main Grid (Votre structure d'origine complétée avec les graphiques et panneaux manquants) */}
        <div className='grid grid-cols-3 gap-4'>
          
          {/* Colonne de gauche (Prend 2/3 de l'écran pour les tableaux et graphiques lourds) */}
          <div className='col-span-2 space-y-4'>
            <DeviceTable devices={devices} />
            <MachinesPanel devices={devices} />
            
            {/* Ligne regroupant vos 3 composants de graphiques */}
            <div className='grid grid-cols-3 gap-4'>
              <TrafficChart packets={packets} />
              <AttackChart alerts={alerts} />
              <ProtocolChart packets={packets} />
            </div>
          </div>
          
          {/* Colonne de droite (Prend 1/3 de l'écran pour la sécurité et le flux en direct) */}
          <div className='space-y-4'>
            <AlertPanel alerts={alerts} />
            <BlockedPanel alerts={alerts} />
            <PacketStream packets={packets} />
          </div>

        </div>

      </div>
    </div>
  );
}