import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { apiFetch } from '../api/client';
import { setToken } from '../auth/storage';
import { GITHUB_LOGIN_URL } from '../config';

const ERROR_MESSAGES: Record<string, string> = {
  access_denied: '你取消了 GitHub 授权，请重试。',
  invalid_state: '登录校验失败（state 不匹配），请重试。',
  oauth_failed: 'GitHub 授权失败，请稍后重试。',
  session_expired: '登录已过期，请重新登录。',
};

export default function LoginPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const error = params.get('error');
  const message = error ? (ERROR_MESSAGES[error] ?? '登录失败，请重试。') : null;
  const [devError, setDevError] = useState<string | null>(null);

  async function devLogin() {
    try {
      const res = await apiFetch<{ token: string }>('/auth/dev-login', { method: 'POST' });
      setToken(res.token);
      navigate('/', { replace: true });
    } catch {
      setDevError('开发登录不可用（仅当后端 ENV=dev 时开启）。');
    }
  }

  return (
    <main className="app">
      <div className="seal-logo">算法<br />道场</div>
      <h1>算法道场 AlgoDojo</h1>
      <p className="tagline">研习算法之道 · 修炼手撕之功</p>
      <div className="cloud-divider">
        <span className="cloud" />
      </div>

      <section className="status">
        <h2>登录</h2>
        {message && (
          <p className="fail" role="alert">
            ⚠️ {message}
          </p>
        )}
        {/* Full-page navigation to the backend so the OAuth state cookie is set
            on the backend origin. */}
        <a className="github-btn" href={GITHUB_LOGIN_URL}>
          使用 GitHub 登录
        </a>
        <p className="hint">仅申请只读用户信息（read:user），不会访问你的仓库。</p>

        <hr />
        <button className="logout-btn" onClick={devLogin}>
          开发登录（验收用，免 GitHub）
        </button>
        {devError && <p className="fail">{devError}</p>}
      </section>
    </main>
  );
}
