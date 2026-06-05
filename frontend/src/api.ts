const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...init,
  });

  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      detail = await response.json();
    } catch {
      /* ignore */
    }
    throw { status: response.status, detail };
  }

  return response.json() as Promise<T>;
}

export type UserProfile = {
  sub?: string;
  email?: string;
  name?: string;
  picture?: string;
};

export type AuthMe = {
  authenticated: boolean;
  user: UserProfile;
};

export type CreditBalance = {
  spendable_cents: number;
  balance_cents: number;
};

export type QuizQuestion = {
  type: "mcq" | "true_false" | "cloze";
  question: string;
  options?: string[];
  answer: string | boolean;
};

export type QuizResult = {
  run_id: string;
  source_name: string;
  created_at: string;
  mode: string;
  quiz: { questions: QuizQuestion[]; count: number };
  analysis: {
    concepts: string[];
    learning_objectives: string[];
    syllabus_tree?: Record<string, unknown>;
  };
  statistics: Record<string, unknown>;
  llm_calls_used: number;
  estimated_cost: number;
  storage_error?: string;
};

export type HistoryDoc = {
  doc_id: string;
  data: {
    runId?: string;
    sourceName?: string;
    createdAt?: string;
    mode?: string;
    questionCount?: number;
  };
  updated_at?: string;
};

export const api = {
  me: () => request<AuthMe>("/auth/me"),
  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),
  balance: () => request<CreditBalance>("/api/credits/balance"),
  usage: () => request<Record<string, unknown>>("/api/storage/usage"),
  history: () => request<{ docs: HistoryDoc[] }>("/api/quizzes/history"),
  generate: (file: File, nQuestions: number, offline: boolean) => {
    const form = new FormData();
    form.append("pdf", file);
    form.append("n_questions", String(nQuestions));
    form.append("offline", String(offline));
    return request<QuizResult>("/api/quizzes/generate", {
      method: "POST",
      body: form,
    });
  },
  loginUrl: () => `${API_BASE}/auth/login`,
};
