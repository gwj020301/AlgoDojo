import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { type CurrentUser, fetchCurrentUser } from '../api/client';
import { clearToken } from '../auth/storage';

export default function Header() {
  const navigate = useNavigate();
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => {
        /* 401 handled by interceptor */
      });
  }, []);

  function logout() {
    clearToken();
    navigate('/login', { replace: true });
  }

  return (
    <header className="topbar">
      <div className="topbar-left">
        <Link to="/" className="brand">
          算法道场
        </Link>
        <nav className="nav">
          <Link to="/">题库</Link>
          <Link to="/roadmap">路线图</Link>
          <Link to="/patterns">套路速查</Link>
        </nav>
      </div>
      <div className="topbar-right">
        {user && <span className="username">{user.username}</span>}
        <button className="logout-btn" onClick={logout}>
          退出
        </button>
      </div>
    </header>
  );
}
