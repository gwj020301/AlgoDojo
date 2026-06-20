import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';

import { isAuthenticated } from '../auth/storage';

/** Renders children only when authenticated; otherwise redirects to /login. */
export default function RequireAuth({ children }: { children: ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
