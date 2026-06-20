import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { setToken } from '../auth/storage';

/**
 * Lands here after GitHub OAuth. The backend redirected to
 * `/auth/callback#token=<jwt>` — read the JWT from the URL fragment, store it,
 * then replace the URL (so the token doesn't linger in history) and go home.
 */
export default function AuthCallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const fragment = window.location.hash.startsWith('#')
      ? window.location.hash.slice(1)
      : window.location.hash;
    const token = new URLSearchParams(fragment).get('token');

    if (token) {
      setToken(token);
      navigate('/', { replace: true });
    } else {
      navigate('/login?error=oauth_failed', { replace: true });
    }
  }, [navigate]);

  return (
    <main className="app">
      <p>登录中…</p>
    </main>
  );
}
