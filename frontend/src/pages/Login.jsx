// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/client';

export default function Login() {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [err,  setErr]  = useState('');
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await login(user, pass);
      localStorage.setItem('se_token', res.data.access_token);
      navigate('/dashboard');
    } catch {
      setErr('Invalid credentials. Please try again.');
    }
  };

  return (
    <div className='min-h-screen flex items-center justify-center'
         style={{background: 'radial-gradient(ellipse at center, #2a0610 0%, #0d0204 100%)'}}
    >
      <div className='bg-white/5 border border-white/10 rounded-2xl p-10 w-96 backdrop-blur-sm'>
        <img src='/logo.png' alt='Secure-Eye' className='h-16 mx-auto mb-6' />
        <h1 className='text-white text-2xl font-bold text-center mb-1'>SECURE-EYE</h1>
        <p className='text-white/40 text-sm text-center mb-8'>Network Monitoring System</p>
        <input className='w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white mb-4 outline-none focus:border-accent'
               placeholder='Administrator Username'
               value={user} onChange={e => setUser(e.target.value)} />
        <input type='password'
               className='w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white mb-4 outline-none focus:border-accent'
               placeholder='Password'
               value={pass} onChange={e => setPass(e.target.value)}
               onKeyDown={e => e.key==='Enter' && handleLogin()} />
        {err && <p className='text-red-400 text-sm mb-4'>{err}</p>}
        <button onClick={handleLogin}
                className='w-full bg-primary hover:bg-red-700 text-white font-bold py-3 rounded-lg transition'>
          SIGN IN
        </button>
      </div>
    </div>
  );
}
