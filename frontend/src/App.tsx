import { useEffect, useMemo, useState } from "react";
import { api, AuthMe, CreditBalance, HistoryDoc, QuizResult } from "./api";

function formatCents(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

export default function App() {
  const [auth, setAuth] = useState<AuthMe | null>(null);
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [history, setHistory] = useState<HistoryDoc[]>([]);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [nQuestions, setNQuestions] = useState(10);
  const [offline, setOffline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canGenerateOnline = useMemo(
    () => offline || (balance?.spendable_cents ?? 0) > 0,
    [offline, balance]
  );

  useEffect(() => {
    bootstrap();
  }, []);

  async function bootstrap() {
    setLoading(true);
    setError(null);
    try {
      const me = await api.me();
      setAuth(me);
      const [bal, hist] = await Promise.all([api.balance(), api.history()]);
      setBalance(bal);
      setHistory(hist.docs || []);
    } catch {
      setAuth(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    await api.logout();
    setAuth(null);
    setBalance(null);
    setHistory([]);
    setResult(null);
  }

  async function handleGenerate() {
    if (!file) {
      setError("Upload a PDF lecture first.");
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      const quiz = await api.generate(file, nQuestions, offline);
      setResult(quiz);
      const [bal, hist] = await Promise.all([api.balance(), api.history()]);
      setBalance(bal);
      setHistory(hist.docs || []);
    } catch (err: unknown) {
      const e = err as { status?: number; detail?: unknown };
      if (e.status === 402) {
        setError("Insufficient paid Ludwitt credits. Top up at pitchrise.ludwitt.com/account/credits");
      } else if (typeof e.detail === "string") {
        setError(e.detail);
      } else {
        setError("Quiz generation failed. Please try again.");
      }
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return <div className="page"><div className="card">Loading QuickQuiz...</div></div>;
  }

  if (!auth?.authenticated) {
    return (
      <div className="page hero">
        <div className="card hero-card">
          <p className="eyebrow">Ludwitt Learning Engineer App</p>
          <h1>Turn lecture PDFs into adaptive quizzes</h1>
          <p className="lede">
            Sign in with Ludwitt to generate AI-powered quizzes, spend paid credits safely,
            and save quiz history in Ludwitt hosted storage.
          </p>
          <a className="button primary" href={api.loginUrl()}>Sign in with Ludwitt</a>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="topbar card">
        <div>
          <p className="eyebrow">QuickQuiz</p>
          <h2>Welcome, {auth.user.name || auth.user.email || "Learner"}</h2>
        </div>
        <div className="topbar-actions">
          <div className="pill">Spendable: {formatCents(balance?.spendable_cents ?? 0)}</div>
          <button className="button ghost" onClick={handleLogout}>Log out</button>
        </div>
      </header>

      <main className="grid">
        <section className="card panel">
          <h3>Generate Quiz</h3>
          <label className="field">
            <span>Lecture PDF</span>
            <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          <label className="field">
            <span>Questions: {nQuestions}</span>
            <input
              type="range"
              min={5}
              max={30}
              step={5}
              value={nQuestions}
              onChange={(e) => setNQuestions(Number(e.target.value))}
            />
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={offline} onChange={(e) => setOffline(e.target.checked)} />
            Offline mode (no AI credits)
          </label>
          {!offline && !canGenerateOnline && (
            <p className="warning">You need paid Ludwitt credits for online AI analysis.</p>
          )}
          {error && <p className="error">{error}</p>}
          <button
            className="button primary"
            disabled={generating || !file || (!offline && !canGenerateOnline)}
            onClick={handleGenerate}
          >
            {generating ? "Generating..." : "Generate Quiz"}
          </button>
        </section>

        <section className="card panel">
          <h3>Recent Quizzes</h3>
          {history.length === 0 ? (
            <p className="muted">No saved quizzes yet.</p>
          ) : (
            <ul className="history-list">
              {history.map((item) => (
                <li key={item.doc_id}>
                  <strong>{item.data.sourceName || item.doc_id}</strong>
                  <span>{item.data.mode || "online"} · {item.data.questionCount || 0} questions</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        {result && (
          <>
            <section className="card panel wide">
              <h3>Quiz Results</h3>
              <p className="muted">{result.source_name} · {result.quiz.count} questions · {result.mode}</p>
              <div className="question-grid">
                {result.quiz.questions.map((q, idx) => (
                  <article key={idx} className="question-card">
                    <p className="tag">{q.type}</p>
                    <p>{q.question}</p>
                    {q.options && (
                      <ul>
                        {q.options.map((opt) => (
                          <li key={opt}>{opt}</li>
                        ))}
                      </ul>
                    )}
                    <p className="answer">Answer: {String(q.answer)}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="card panel">
              <h3>Learning Analysis</h3>
              <p><strong>Concepts:</strong> {result.analysis.concepts.join(", ") || "None"}</p>
              <ul>
                {result.analysis.learning_objectives.map((obj) => (
                  <li key={obj}>{obj}</li>
                ))}
              </ul>
            </section>

            <section className="card panel">
              <h3>Metrics</h3>
              <p>LLM calls: {result.llm_calls_used}</p>
              <p>Estimated cost: ${result.estimated_cost.toFixed(4)}</p>
              {result.storage_error && <p className="warning">Storage warning: {result.storage_error}</p>}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
