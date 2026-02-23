// SOOP API config - set these in Vercel environment variables
// For local dev, change these values
export const SOOP_CLIENT_ID = import.meta.env.VITE_SOOP_CLIENT_ID || ''
export const SOOP_CLIENT_SECRET = import.meta.env.VITE_SOOP_CLIENT_SECRET || ''
export const SOOP_REDIRECT_URI = import.meta.env.VITE_SOOP_REDIRECT_URI || window.location.origin + '/redirect'
export const API_BASE = import.meta.env.VITE_API_BASE || ''
