import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  type Progress,
  type ProblemFilters,
  type ProblemStatus,
  type TopicGroup,
  getProgress,
  listProblems,
} from '../api/client';
import Header from '../components/Header';

const STATUS_LABEL: Record<ProblemStatus, string> = {
  not_started: '未开始',
  in_progress: '进行中',
  passed: '已通过',
};

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
};

export default function ProblemListPage() {
  const [groups, setGroups] = useState<TopicGroup[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [difficulty, setDifficulty] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const filters: ProblemFilters = {};
    if (difficulty) filters.difficulty = difficulty;
    if (status) filters.status = status as ProblemStatus;

    setLoading(true);
    listProblems(filters)
      .then((g) => {
        setGroups(g);
        setError(null);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [difficulty, status]);

  useEffect(() => {
    getProgress()
      .then(setProgress)
      .catch(() => {
        /* ignore */
      });
  }, []);

  return (
    <div>
      <Header />
      <main className="page">
        <div className="page-head">
          <h1>题库</h1>
          {progress && (
            <span className="progress-pill">
              已通过 {progress.passed}/{progress.total_problems}（
              {Math.round(progress.completion_rate * 100)}%）
            </span>
          )}
        </div>

        <div className="filters">
          <label>
            难度：
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="">全部</option>
              <option value="easy">简单</option>
              <option value="medium">中等</option>
              <option value="hard">困难</option>
            </select>
          </label>
          <label>
            状态：
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">全部</option>
              <option value="not_started">未开始</option>
              <option value="in_progress">进行中</option>
              <option value="passed">已通过</option>
            </select>
          </label>
        </div>

        {loading && <p>加载中…</p>}
        {error && <p className="fail">加载失败：{error}</p>}
        {!loading && !error && groups.length === 0 && <p>没有符合条件的题目。</p>}

        {groups.map((group) => (
          <section key={group.topic_id} className="topic-group">
            <h2>{group.topic_name}</h2>
            <ul className="problem-list">
              {group.problems.map((p) => (
                <li key={p.id} className="problem-row">
                  <Link to={`/problems/${p.id}`} className="problem-link">
                    <span className="problem-number">{p.number}.</span>
                    <span className="problem-title">{p.title}</span>
                  </Link>
                  <span className={`badge difficulty-${p.difficulty}`}>
                    {DIFFICULTY_LABEL[p.difficulty] ?? p.difficulty}
                  </span>
                  <span className={`badge status-${p.status}`}>{STATUS_LABEL[p.status]}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </main>
    </div>
  );
}
