import client from './client'

// Fetch live network stats
export const getStats     = ()  => client.get('/stats').then(r => r.data)

// Fetch recent alerts (last 50 by default)
export const getAlerts    = ()  => client.get('/alerts').then(r => r.data)

// Fetch all blocked IPs
export const getBlocked   = ()  => client.get('/blocked').then(r => r.data)

// Unblock a specific IP
export const unblockIP    = (ip) => client.delete(`/blocked/${ip}`).then(r => r.data)

// Block an IP manually
export const blockIP      = (ip) => client.post('/block', { ip }).then(r => r.data)

// Fetch list of monitored machines
export const getMachines  = ()  => client.get('/machines').then(r => r.data)

// Toggle prevention mode on/off
export const setPrevention = (enabled) =>
  client.post('/prevention', { enabled }).then(r => r.data)

// Get current prevention status
export const getPreventionStatus = () =>
  client.get('/prevention').then(r => r.data)