import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { type Pattern, getPatterns } from '../api/client';
import Header from '../components/Header';

export default function PatternsPage() {
  const [params, setParams] = useSearchParams();
  const initialQ = params.get('q') ?? '';
  const [query, setQuery] = useState(initialQ);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const q = params.get('q') ?? '';
    getPatterns(q || undefined)
      .then(setPatterns)
      .catch((e: Error) => setError(e.message));
  }, [params]);

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    setParams(query ? { q: query } : {});
  }

  return (
    <div>
      <Header />
      <main className="page">
        <h1>套路速查</h1>
        <form className="search" onSubmit={onSearch}>
          <input
            type="text"
            placeholder="搜索套路（如：滑动窗口、二分）"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit">搜索</button>
        </form>

        {error && <p className="fail">加载失败：{error}</p>}
        {patterns.length === 0 && !error && <p>没有匹配的套路。</p>}

        {patterns.map((p) => (
          <PatternCard key={p.pattern_name} pattern={p} />
        ))}
      </main>
    </div>
  );
}

function PatternCard({ pattern }: { pattern: Pattern }) {
  const languages = Object.keys(pattern.templates);
  const [lang, setLang] = useState(languages[0] ?? '');

  return (
    <section className="pattern-card">
      <div className="pattern-head">
        <h2>{pattern.pattern_name}</h2>
        <div className="lang-tabs">
          {languages.map((l) => (
            <button
              key={l}
              className={l === lang ? 'active' : ''}
              onClick={() => setLang(l)}
            >
              {l}
            </button>
          ))}
        </div>
      </div>
      {pattern.mnemonic && <p className="mnemonic">💡 {pattern.mnemonic}</p>}
      <pre className="pattern-code">
        <code>{pattern.templates[lang]}</code>
      </pre>
    </section>
  );
}
