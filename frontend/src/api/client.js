// src/api/client.js
import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://secure-eye-backend.onrender.com',
});

API.interceptors.request.use(config => {
  const token = localStorage.getItem('se_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const login = (u, p) =>
  API.post('/auth/token', new URLSearchParams({ username: u, password: p }),
           { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });

export const getDevices = () => API.get('/devices');
export const predict    = (payload) => API.post('/predict', payload);

export default API;
