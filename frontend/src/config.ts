// Frontend runtime configuration.

// Backend origin, used ONLY for the full-page GitHub OAuth redirect so the CSRF
// state cookie is set on (and returned to) the backend origin. XHR/fetch calls
// instead go through the Vite dev proxy at `/api` (same-origin, no CORS).
export const BACKEND_URL: string =
  (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? 'http://localhost:8000';

// Base path for API calls made via fetch (proxied to the backend in dev).
export const API_BASE = '/api';

// URL the "Login with GitHub" button sends the browser to.
export const GITHUB_LOGIN_URL = `${BACKEND_URL}/auth/github/login`;
