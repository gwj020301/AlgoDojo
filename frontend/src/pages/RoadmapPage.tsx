import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { type RoadmapTopic, getRoadmap } from '../api/client';
import Header from '../components/Header';

const STATUS_DOT: Record<string, string> = {
  not_started: '○',
  in_progress: '◐',
  passed: '●',
};

export default function RoadmapPage() {
  const [topics, setTopics] = useState<RoadmapTopic[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRoadmap()
      .then(setTopics)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div>
      <Header />
      <main className="page">
        <h1>专题路线图</h1>
        <p className="hint">按难度梯度循序渐进：从哈希、双指针到动态规划。</p>
        {error && <p className="fail">加载失败：{error}</p>}

        <ol className="roadmap">
          {topics.map((t) => (
            <li key={t.topic_id} className="roadmap-node">
              <div className="roadmap-head">
                <h2>
                  {t.order_index + 1}. {t.name}
                </h2>
                <span className="progress-pill">
                  {t.passed}/{t.total}（{Math.round(t.completion_rate * 100)}%）
                </span>
              </div>
              {t.pattern_summary && <p className="pattern-summary">{t.pattern_summary}</p>}
              <ul className="rec-problems">
                {t.problems.map((p) => (
                  <li key={p.id}>
                    <span className={`status-dot status-${p.status}`}>
                      {STATUS_DOT[p.status]}
                    </span>
                    <Link to={`/problems/${p.id}`}>
                      {p.number}. {p.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </main>
    </div>
  );
}
