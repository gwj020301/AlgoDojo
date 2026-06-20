import Editor from '@monaco-editor/react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  type HintsState,
  type ProblemDetail,
  type Submission,
  createSubmission,
  getHints,
  getProblem,
  getSubmission,
  unlockHint,
} from '../api/client';
import Header from '../components/Header';

const HINT_LEVEL_LABEL: Record<number, string> = {
  1: '思路方向',
  2: '关键步骤',
  3: '伪代码',
  4: '完整题解',
};

const MONACO_LANG: Record<string, string> = {
  python: 'python',
  typescript: 'typescript',
};

const STATUS_LABEL: Record<string, string> = {
  queued: '排队中…',
  running: '执行中…',
  done: '完成',
  system_error: '判题系统错误',
};

const VERDICT_LABEL: Record<string, string> = {
  AC: '✅ 通过 (Accepted)',
  WA: '❌ 答案错误 (Wrong Answer)',
  TLE: '⏱️ 超时 (Time Limit Exceeded)',
  MLE: '💾 内存超限 (Memory Limit Exceeded)',
  CE: '🛠️ 编译错误 (Compile Error)',
  RE: '💥 运行时错误 (Runtime Error)',
};

function draftKey(problemId: number, language: string): string {
  return `algodojo_draft_${problemId}_${language}`;
}

export default function ProblemPage() {
  const { id } = useParams<{ id: string }>();
  const problemId = Number(id);

  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [language, setLanguage] = useState<string>('');
  const [code, setCode] = useState<string>('');
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hints, setHints] = useState<HintsState | null>(null);
  const [hintsOpen, setHintsOpen] = useState(false);

  const pollRef = useRef<number | null>(null);

  // Load the saved draft for a language, falling back to the template.
  const loadCodeFor = useCallback(
    (p: ProblemDetail, lang: string): string => {
      const draft = localStorage.getItem(draftKey(p.id, lang));
      if (draft != null) return draft;
      return p.templates[lang] ?? '';
    },
    [],
  );

  useEffect(() => {
    getProblem(problemId)
      .then((p) => {
        setProblem(p);
        const lang = p.languages[0] ?? 'python';
        setLanguage(lang);
        setCode(loadCodeFor(p, lang));
      })
      .catch((e: Error) => setError(e.message));
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [problemId, loadCodeFor]);

  function onCodeChange(value: string | undefined) {
    const next = value ?? '';
    setCode(next);
    if (problem) localStorage.setItem(draftKey(problem.id, language), next);
  }

  function onLanguageChange(nextLang: string) {
    if (!problem || nextLang === language) return;
    // Requirement 3.3: warn before switching that current code may be replaced.
    if (code.trim() !== '' && !window.confirm('切换语言会加载该语言的草稿/模板，确定切换吗？')) {
      return;
    }
    setLanguage(nextLang);
    setCode(loadCodeFor(problem, nextLang));
  }

  function startPolling(submissionId: string) {
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      try {
        const s = await getSubmission(submissionId);
        setSubmission(s);
        if (s.status === 'done' || s.status === 'system_error') {
          if (pollRef.current) window.clearInterval(pollRef.current);
          pollRef.current = null;
          setRunning(false);
        }
      } catch {
        if (pollRef.current) window.clearInterval(pollRef.current);
        pollRef.current = null;
        setRunning(false);
      }
    }, 1000);
  }

  function openHints() {
    setHintsOpen(true);
    if (!hints) {
      getHints(problemId)
        .then(setHints)
        .catch((e: Error) => setError(e.message));
    }
  }

  async function unlockNextHint() {
    if (!hints || hints.next_level == null) return;
    if (
      hints.next_is_full_solution &&
      !window.confirm('即将解锁「完整题解」。建议先独立思考，确定查看吗？')
    ) {
      return;
    }
    try {
      const updated = await unlockHint(problemId, hints.next_level);
      setHints(updated);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function run(sampleOnly: boolean) {
    if (!problem || running) return;
    setRunning(true);
    setSubmission(null);
    setError(null);
    try {
      const accepted = await createSubmission({
        problem_id: problem.id,
        language,
        code,
        sample_only: sampleOnly,
      });
      setSubmission({
        id: accepted.id,
        problem_id: problem.id,
        language,
        status: accepted.status,
        verdict: null,
        runtime_ms: null,
        failed_case: null,
        detail: null,
        created_at: new Date().toISOString(),
      });
      startPolling(accepted.id);
    } catch (e) {
      setError((e as Error).message);
      setRunning(false);
    }
  }

  if (error) return <Wrapper><p className="fail">出错了：{error}</p></Wrapper>;
  if (!problem) return <Wrapper><p>加载中…</p></Wrapper>;

  return (
    <Wrapper>
      <div className="problem-layout">
        <section className="problem-desc">
          <h1>
            {problem.number}. {problem.title}
          </h1>
          <div className="meta">
            <span className={`badge difficulty-${problem.difficulty}`}>{problem.difficulty}</span>
            <span className="topic-tag">{problem.topic_name}</span>
          </div>
          <p className="desc-text">{problem.description}</p>

          {problem.samples.length > 0 && (
            <div className="samples">
              <h3>样例</h3>
              {problem.samples.map((s, i) => (
                <div key={i} className="sample-case">
                  <div className="sample-label">样例 {i + 1}</div>
                  <pre>输入：{s.input}</pre>
                  <pre>输出：{s.expected_output}</pre>
                </div>
              ))}
            </div>
          )}

          <div className="learn-links">
            <Link to={`/patterns?q=${encodeURIComponent(problem.topic_name)}`} className="pattern-link">
              查看「{problem.topic_name}」相关套路 →
            </Link>
          </div>

          <div className="hints-box">
            {!hintsOpen ? (
              <button className="hint-toggle" onClick={openHints}>
                💡 需要提示？
              </button>
            ) : (
              <div className="hints-panel">
                <h3>分层提示</h3>
                {hints == null && <p>加载中…</p>}
                {hints && hints.total_levels === 0 && <p className="hint">本题暂无提示。</p>}
                {hints &&
                  hints.unlocked.map((h) => (
                    <div key={h.level} className="hint-item">
                      <strong>
                        {h.level}. {HINT_LEVEL_LABEL[h.level] ?? `提示 ${h.level}`}
                      </strong>
                      <p>{h.content}</p>
                    </div>
                  ))}
                {hints && hints.next_level != null && (
                  <button className="hint-unlock-btn" onClick={unlockNextHint}>
                    解锁下一层（{HINT_LEVEL_LABEL[hints.next_level] ?? hints.next_level}）
                    {hints.next_is_full_solution ? ' ⚠️' : ''}
                  </button>
                )}
                {hints && hints.next_level == null && hints.total_levels > 0 && (
                  <p className="hint">已解锁全部提示。</p>
                )}
              </div>
            )}
          </div>
        </section>

        <section className="problem-editor">
          <div className="editor-toolbar">
            <select value={language} onChange={(e) => onLanguageChange(e.target.value)}>
              {problem.languages.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
            <div className="actions">
              <button onClick={() => run(true)} disabled={running} className="run-btn">
                运行（样例）
              </button>
              <button onClick={() => run(false)} disabled={running} className="submit-btn">
                提交
              </button>
            </div>
          </div>

          <div className="editor-host">
            <Editor
              height="100%"
              theme="vs-dark"
              language={MONACO_LANG[language] ?? 'plaintext'}
              value={code}
              onChange={onCodeChange}
              options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false }}
            />
          </div>

          <ResultPanel submission={submission} running={running} />
        </section>
      </div>
    </Wrapper>
  );
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <Header />
      <main className="page">{children}</main>
    </div>
  );
}

function ResultPanel({ submission, running }: { submission: Submission | null; running: boolean }) {
  if (!submission && !running) {
    return <div className="result-panel muted">点击「运行」用样例自测，或「提交」对全部用例判题。</div>;
  }
  if (!submission) return <div className="result-panel">提交中…</div>;

  const { status, verdict, runtime_ms, failed_case, detail } = submission;

  if (status !== 'done') {
    return (
      <div className="result-panel">
        <strong>{STATUS_LABEL[status] ?? status}</strong>
        {status === 'system_error' && detail && <p className="fail">{detail}</p>}
      </div>
    );
  }

  const isAc = verdict === 'AC';
  return (
    <div className={`result-panel ${isAc ? 'result-ok' : 'result-bad'}`}>
      <strong>{verdict ? (VERDICT_LABEL[verdict] ?? verdict) : '完成'}</strong>
      {runtime_ms != null && <span className="runtime"> · {runtime_ms} ms</span>}
      {failed_case && (
        <div className="failed-case">
          <div>失败用例 #{failed_case.index}</div>
          <pre>输入：{failed_case.input}</pre>
          <pre>期望：{failed_case.expected}</pre>
          <pre>实际：{failed_case.actual}</pre>
        </div>
      )}
      {!failed_case && detail && <pre className="detail">{detail}</pre>}
    </div>
  );
}
