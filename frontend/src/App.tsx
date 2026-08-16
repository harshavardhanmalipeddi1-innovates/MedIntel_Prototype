import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  Activity,
  ClipboardPlus,
  FileText,
  LayoutDashboard,
  Menu,
  Moon,
  Settings,
  ShieldCheck,
  Stethoscope,
  Sun,
  Users,
  X,
} from "lucide-react";
import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import "./styles.css";
import {
  clearClinicianSession,
  getAssessmentQuestionnaire,
  getCurrentClinician,
  getStoredClinicianSession,
  loginClinician,
  prepareAssessment,
  runClinicalWorkflow,
  runVerifiedSyntheticWorkflow,
  subscribeClinicianSession,
  type AssessmentQuestion,
  type AssessmentQuestionnaire,
  type ClinicianSession,
  type WorkflowResponse,
} from "./api";

type PageMeta = {
  title: string;
  eyebrow: string;
  description: string;
};

const pages: Record<string, PageMeta> = {
  dashboard: {
    title: "Clinical Dashboard",
    eyebrow: "MedIntel Workspace",
    description:
      "A clinician-controlled workspace for structured assessment and AI-assisted decision support.",
  },
  patients: {
    title: "Patients",
    eyebrow: "Patient Workspace",
    description:
      "Patient search, selection, history, and longitudinal records will be implemented in this phase.",
  },
  assessment: {
    title: "New Clinical Assessment",
    eyebrow: "Structured Intake",
    description:
      "Capture demographics, symptoms, history, vitals, examination findings, and model-compatible evidence.",
  },
  decision: {
    title: "AI Decision Support",
    eyebrow: "Clinician Review",
    description:
      "Review authoritative XGBoost differentials and constrained MedGemma reasoning without allowing ranking drift.",
  },
  reports: {
    title: "Reports",
    eyebrow: "Clinical Documentation",
    description:
      "Structured report drafting and export will be added after the assessment and review workflow is connected.",
  },
  settings: {
    title: "Settings",
    eyebrow: "Workspace Configuration",
    description:
      "Configure clinician preferences, integrations, and future authentication controls.",
  },
};

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/patients", label: "Patients", icon: Users },
  { to: "/assessment", label: "New Assessment", icon: ClipboardPlus },
  { to: "/decision-support", label: "AI Decision Support", icon: Stethoscope },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];


function AuthLoadingScreen() {
  return (
    <div className="auth-screen theme-dark">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="brand-mark">
            <ShieldCheck size={22} />
          </div>

          <div>
            <span className="eyebrow">MedIntel</span>
            <h1>Verifying clinician session</h1>
          </div>
        </div>

        <p className="auth-description">
          Confirming the local clinician access boundary before opening
          decision-support tools.
        </p>

        <div className="auth-loading-row">
          <Activity size={19} className="spin" />
          <span>Checking authenticated session...</span>
        </div>
      </section>
    </div>
  );
}

function ClinicianLoginPage({
  onAuthenticated,
}: {
  onAuthenticated: (session: ClinicianSession) => void;
}) {
  const [username, setUsername] = useState("clinician");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogin(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const normalizedUsername = username.trim();

    if (!normalizedUsername || !password) {
      setError("Enter the clinician username and password.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const session = await loginClinician(
        normalizedUsername,
        password,
      );

      setPassword("");
      onAuthenticated(session);
    } catch {
      setError(
        "Sign-in failed. Check the clinician credentials and try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen theme-dark">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="brand-mark">
            <ShieldCheck size={22} />
          </div>

          <div>
            <span className="eyebrow">MedIntel</span>
            <h1>Clinician sign in</h1>
          </div>
        </div>

        <p className="auth-description">
          Local research-prototype access for the clinician-controlled
          respiratory decision-support workspace.
        </p>

        <form
          className="auth-form"
          onSubmit={handleLogin}
        >
          <label>
            <span>Clinician username</span>
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) =>
                setUsername(event.target.value)
              }
              disabled={submitting}
              maxLength={128}
              required
            />
          </label>

          <label>
            <span>Password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              disabled={submitting}
              maxLength={256}
              required
            />
          </label>

          {error && (
            <div
              className="auth-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            className="button button-primary auth-submit"
            type="submit"
            disabled={
              submitting ||
              !username.trim() ||
              !password
            }
          >
            {submitting
              ? "Signing in..."
              : "Sign in to clinician workspace"}
          </button>
        </form>

        <div className="auth-safety-note">
          <ShieldCheck size={18} />

          <p>
            Authentication controls access only. MedIntel remains
            clinical decision support; diagnosis and treatment decisions
            remain with the doctor.
          </p>
        </div>
      </section>
    </div>
  );
}

function AppShell() {
  const [session, setSession] =
    useState<ClinicianSession | null>(
      () => getStoredClinicianSession(),
    );

  const [authChecking, setAuthChecking] =
    useState(
      () => getStoredClinicianSession() !== null,
    );

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, setDark] = useState(true);

  const shellClass = useMemo(
    () => `app-shell ${dark ? "theme-dark" : "theme-light"}`,
    [dark],
  );

  useEffect(() => {
    return subscribeClinicianSession(() => {
      setSession(
        getStoredClinicianSession(),
      );
    });
  }, []);

  useEffect(() => {
    if (!session) {
      setAuthChecking(false);
      return;
    }

    let cancelled = false;

    setAuthChecking(true);

    void getCurrentClinician()
      .then((identity) => {
        if (cancelled) {
          return;
        }

        if (
          identity.role !== "clinician" ||
          identity.username !== session.clinician.username
        ) {
          clearClinicianSession();
          setSession(null);
          setAuthChecking(false);
          return;
        }

        setAuthChecking(false);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        clearClinicianSession();
        setSession(null);
        setAuthChecking(false);
      });

    return () => {
      cancelled = true;
    };
  }, [session]);

  function handleLogout() {
    clearClinicianSession();
    setSession(null);
    setSidebarOpen(false);
  }

  if (authChecking) {
    return <AuthLoadingScreen />;
  }

  if (!session) {
    return (
      <ClinicianLoginPage
        onAuthenticated={(nextSession) => {
          setAuthChecking(true);
          setSession(nextSession);
        }}
      />
    );
  }


  return (
    <div className={shellClass}>
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark">
            <Activity size={23} strokeWidth={2.2} />
          </div>
          <div>
            <strong>MedIntel</strong>
            <span>Clinical Decision Support</span>
          </div>
          <button
            className="icon-button sidebar-close"
            type="button"
            aria-label="Close navigation"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="primary-nav" aria-label="Primary navigation">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-item-active" : ""}`
              }
            >
              <Icon size={19} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-safety">
          <ShieldCheck size={18} />
          <div>
            <strong>Clinician authority</strong>
            <span>AI output requires doctor review.</span>
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation"
          type="button"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <main className="main-area">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            type="button"
            aria-label="Open navigation"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={21} />
          </button>

          <div className="topbar-status">
            <span className="status-dot" />
            <span>Phase 5 - Frontend implementation</span>
          </div>

          <div className="topbar-actions">
            <button
              className="icon-button"
              type="button"
              aria-label={dark ? "Use light theme" : "Use dark theme"}
              onClick={() => setDark((value) => !value)}
            >
              {dark ? <Sun size={19} /> : <Moon size={19} />}
            </button>
            <div className="doctor-chip" aria-label="Authenticated clinician">
              <div className="doctor-avatar">DR</div>
              <div>
                <strong>{session.clinician.username}</strong>
                <span>Authenticated clinician</span>
              </div>
            </div>

            <button
              className="button button-secondary auth-logout-button"
              type="button"
              onClick={handleLogout}
            >
              Sign out
            </button>
          </div>
        </header>

        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route
            path="/patients"
            element={<PlaceholderPage meta={pages.patients} />}
          />
          <Route
            path="/assessment"
            element={<AssessmentPage />}
          />
          <Route
            path="/decision-support"
            element={<DecisionSupportPage />}
          />
          <Route
            path="/reports"
            element={<PlaceholderPage meta={pages.reports} />}
          />
          <Route
            path="/settings"
            element={<PlaceholderPage meta={pages.settings} />}
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function PageHeader({ meta }: { meta: PageMeta }) {
  return (
    <section className="page-header">
      <div>
        <span className="eyebrow">{meta.eyebrow}</span>
        <h1>{meta.title}</h1>
        <p>{meta.description}</p>
      </div>
      <div className="safety-pill">
        <ShieldCheck size={17} />
        Decision support only
      </div>
    </section>
  );
}

function Dashboard() {
  return (
    <div className="page">
      <PageHeader meta={pages.dashboard} />

      <section className="hero-panel">
        <div>
          <span className="hero-kicker">Doctor-first workflow</span>
          <h2>Move from structured assessment to reviewed AI support.</h2>
          <p>
            Phase 5 connects the existing FastAPI, XGBoost, and local MedGemma
            workflow to a clear clinician interface while preserving model
            authority and safety constraints.
          </p>
          <div className="hero-actions">
            <NavLink className="button button-primary" to="/assessment">
              <ClipboardPlus size={18} />
              Start assessment
            </NavLink>
            <NavLink className="button button-secondary" to="/decision-support">
              <Stethoscope size={18} />
              Review AI workspace
            </NavLink>
          </div>
        </div>
        <div className="hero-guardrail">
          <ShieldCheck size={30} />
          <strong>Clinical guardrail</strong>
          <p>
            XGBoost remains authoritative for candidates, ranks, and
            probabilities. MedGemma cannot alter them.
          </p>
        </div>
      </section>

      <section className="metric-grid" aria-label="Implementation status">
        <StatusCard
          label="Backend API"
          value="Ready"
          note="FastAPI workflow available"
        />
        <StatusCard
          label="XGBoost"
          value="Authoritative"
          note="Ranked differential engine"
        />
        <StatusCard
          label="MedGemma"
          value="Local"
          note="Constrained reasoning via llama.cpp"
        />
        <StatusCard
          label="Frontend"
          value="Phase 5"
          note="Implementation started"
        />
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Planned workflow</span>
              <h3>Clinical assessment path</h3>
            </div>
          </div>
          <div className="workflow-list">
            {[
              ["01", "Patient context", "Demographics and encounter context"],
              ["02", "Clinical assessment", "Symptoms, history, vitals, examination"],
              ["03", "XGBoost ranking", "Authoritative differential candidates"],
              ["04", "MedGemma reasoning", "Constrained context around existing candidates"],
              ["05", "Doctor review", "Explicit clinician approval remains mandatory"],
            ].map(([step, title, note]) => (
              <div className="workflow-item" key={step}>
                <span>{step}</span>
                <div>
                  <strong>{title}</strong>
                  <p>{note}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <span className="eyebrow">Current scope</span>
          <h3>What Phase 5 will add</h3>
          <ul className="check-list">
            <li>Responsive clinician dashboard</li>
            <li>Structured assessment form</li>
            <li>Backend workflow API integration</li>
            <li>Top-ranked differential visualization</li>
            <li>Critical considerations separated from ranking</li>
            <li>Constrained MedGemma reasoning presentation</li>
            <li>Doctor review and approval controls</li>
          </ul>
        </div>
      </section>
    </div>
  );
}

function StatusCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <article className="status-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{note}</p>
    </article>
  );
}


type AssessmentValue = string | boolean | number | string[];

function AssessmentPage() {
  const navigate = useNavigate();

  const [questionnaire, setQuestionnaire] =
    useState<AssessmentQuestionnaire | null>(null);

  const [age, setAge] = useState(45);
  const [sex, setSex] = useState<"M" | "F">("M");
  const [initialEvidence, setInitialEvidence] = useState("");
  const [answers, setAnswers] =
    useState<Record<string, AssessmentValue>>({});
  const [questionSearch, setQuestionSearch] = useState("");

  const [loadingQuestionnaire, setLoadingQuestionnaire] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadQuestionnaire() {
      try {
        const response = await getAssessmentQuestionnaire();

        if (!active) {
          return;
        }

        setQuestionnaire(response);
        setInitialEvidence(response.initial_evidence_codes[0] ?? "");
      } catch (requestError) {
        if (!active) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load the assessment questionnaire.",
        );
      } finally {
        if (active) {
          setLoadingQuestionnaire(false);
        }
      }
    }

    void loadQuestionnaire();

    return () => {
      active = false;
    };
  }, []);

  const visibleQuestions = useMemo(() => {
    if (!questionnaire) {
      return [];
    }

    const search = questionSearch.trim().toLowerCase();

    return questionnaire.questions.filter((question) => {
      if (question.code === initialEvidence) {
        return false;
      }

      if (!search) {
        return true;
      }

      return (
        question.code.toLowerCase().includes(search) ||
        question.question.toLowerCase().includes(search)
      );
    });
  }, [initialEvidence, questionSearch, questionnaire]);

  function updateAnswer(
    code: string,
    value: AssessmentValue | null,
  ) {
    setAnswers((current) => {
      const next = { ...current };

      if (
        value === null ||
        value === "" ||
        (Array.isArray(value) && value.length === 0)
      ) {
        delete next[code];
      } else {
        next[code] = value;
      }

      return next;
    });
  }

  function renderAnswerControl(question: AssessmentQuestion) {
    const value = answers[question.code];

    if (question.answer_kind === "binary") {
      return (
        <select
          className="assessment-input"
          value={typeof value === "boolean" ? String(value) : ""}
          onChange={(event) => {
            if (event.target.value === "") {
              updateAnswer(question.code, null);
              return;
            }

            updateAnswer(
              question.code,
              event.target.value === "true",
            );
          }}
        >
          <option value="">Not answered</option>
          {question.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    if (question.answer_kind === "scale") {
      return (
        <input
          className="assessment-input"
          type="number"
          min={question.scale_min ?? undefined}
          max={question.scale_max ?? undefined}
          step={1}
          value={typeof value === "number" ? value : ""}
          placeholder={
            question.scale_min !== null && question.scale_max !== null
              ? `${question.scale_min} - ${question.scale_max}`
              : "Enter value"
          }
          onChange={(event) => {
            updateAnswer(
              question.code,
              event.target.value === ""
                ? null
                : Number(event.target.value),
            );
          }}
        />
      );
    }

    if (question.answer_kind === "multi_select") {
      const selected = Array.isArray(value) ? value : [];

      return (
        <div className="assessment-options">
          {question.options.map((option) => {
            const checked = selected.includes(option.value);

            return (
              <label
                className="assessment-option"
                key={option.value}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(event) => {
                    const next = event.target.checked
                      ? [...selected, option.value]
                      : selected.filter(
                          (selectedValue) =>
                            selectedValue !== option.value,
                        );

                    updateAnswer(
                      question.code,
                      next.length > 0 ? next : null,
                    );
                  }}
                />
                <span>{option.label}</span>
              </label>
            );
          })}
        </div>
      );
    }

    if (question.options.length > 0) {
      return (
        <select
          className="assessment-input"
          value={typeof value === "string" ? value : ""}
          onChange={(event) =>
            updateAnswer(
              question.code,
              event.target.value || null,
            )
          }
        >
          <option value="">Not answered</option>
          {question.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    return (
      <input
        className="assessment-input"
        type="text"
        value={typeof value === "string" ? value : ""}
        placeholder="Not answered"
        onChange={(event) =>
          updateAnswer(
            question.code,
            event.target.value || null,
          )
        }
      />
    );
  }

  async function submitAssessment(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!initialEvidence) {
      setError("Select an initial evidence before continuing.");
      return;
    }

    setRunning(true);
    setError(null);

    try {
      const assessmentAnswers = Object.entries(answers)
        .filter(([code]) => code !== initialEvidence)
        .map(([code, value]) => ({
          code,
          value,
        }));

      const prepared = await prepareAssessment({
        age,
        sex,
        initial_evidence: initialEvidence,
        answers: assessmentAnswers,
      });

      if (!prepared.patient_context) {
        throw new Error(
          "Assessment preparation returned no patient_context.",
        );
      }

      const workflow =
        await runClinicalWorkflow(prepared.patient_context);

      navigate("/decision-support", {
        state: {
          workflowResult: workflow,
        },
      });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Assessment workflow failed.",
      );
    } finally {
      setRunning(false);
    }
  }

  if (loadingQuestionnaire) {
    return (
      <div className="page">
        <PageHeader meta={pages.assessment} />

        <section className="model-progress">
          <Activity size={20} className="spin" />
          <div>
            <strong>Loading model-scoped questionnaire</strong>
            <p>
              MedIntel is loading the live assessment contract from
              the backend.
            </p>
          </div>
        </section>
      </div>
    );
  }

  if (!questionnaire) {
    return (
      <div className="page">
        <PageHeader meta={pages.assessment} />

        <section className="clinical-error">
          <strong>Assessment questionnaire unavailable</strong>
          <p>{error ?? "The questionnaire could not be loaded."}</p>
        </section>
      </div>
    );
  }

  return (
    <div className="page">
      <PageHeader meta={pages.assessment} />

      <form onSubmit={submitAssessment}>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Step 1</span>
              <h3>Patient and encounter context</h3>
            </div>
          </div>

          <div className="assessment-grid">
            <label className="assessment-field">
              <span>Age</span>
              <input
                className="assessment-input"
                type="number"
                min={0}
                max={120}
                required
                value={age}
                onChange={(event) =>
                  setAge(Number(event.target.value))
                }
              />
            </label>

            <label className="assessment-field">
              <span>Sex</span>
              <select
                className="assessment-input"
                value={sex}
                onChange={(event) =>
                  setSex(event.target.value as "M" | "F")
                }
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </label>

            <label className="assessment-field assessment-field-wide">
              <span>Initial evidence / reason for consultation</span>

              <select
                className="assessment-input"
                required
                value={initialEvidence}
                onChange={(event) => {
                  const code = event.target.value;

                  setInitialEvidence(code);

                  if (code) {
                    updateAnswer(code, null);
                  }
                }}
              >
                <option value="">Select initial evidence</option>

                {questionnaire.initial_evidence_codes.map((code) => {
                  const question = questionnaire.questions.find(
                    (item) => item.code === code,
                  );

                  return (
                    <option key={code} value={code}>
                      {question
                        ? `${code} - ${question.question}`
                        : code}
                    </option>
                  );
                })}
              </select>
            </label>
          </div>
        </section>

        <section className="panel assessment-questionnaire">
          <div className="assessment-toolbar">
            <div>
              <span className="eyebrow">Step 2</span>
              <h3>Model-scoped clinical questionnaire</h3>
              <p>
                Answer only information that is actually known.
                Unanswered items are not submitted to the model.
              </p>
            </div>

            <div className="assessment-count">
              {Object.keys(answers).length} answered
            </div>
          </div>

          <input
            className="assessment-input assessment-search"
            type="search"
            value={questionSearch}
            placeholder="Search questionnaire by evidence code or question"
            onChange={(event) =>
              setQuestionSearch(event.target.value)
            }
          />

          <div className="assessment-question-list">
            {visibleQuestions.map((question) => (
              <article
                className="assessment-question"
                key={question.code}
              >
                <div className="assessment-question-heading">
                  <div>
                    <span className="question-code">
                      {question.code}
                    </span>
                    <strong>{question.question}</strong>
                  </div>

                  <span className="question-kind">
                    {question.answer_kind.replaceAll("_", " ")}
                  </span>
                </div>

                <div className="assessment-control">
                  {renderAnswerControl(question)}
                </div>
              </article>
            ))}
          </div>
        </section>

        {error && (
          <section className="clinical-error">
            <strong>Assessment workflow failed</strong>
            <p>{error}</p>
          </section>
        )}

        <section className="assessment-submit-panel">
          <div>
            <ShieldCheck size={22} />
            <div>
              <strong>Doctor review remains mandatory</strong>
              <p>
                This prepares model input and requests decision support.
                It does not establish a diagnosis or authorize treatment.
              </p>
            </div>
          </div>

          <button
            className="button button-primary workflow-run-button"
            type="submit"
            disabled={running || !initialEvidence}
          >
            <Activity
              size={18}
              className={running ? "spin" : ""}
            />

            {running
              ? "Running decision support..."
              : "Prepare assessment & run decision support"}
          </button>
        </section>

        {running && (
          <section className="model-progress">
            <Activity size={20} className="spin" />
            <div>
              <strong>
                XGBoost and constrained local reasoning are running
              </strong>
              <p>
                Local CPU reasoning can require several minutes.
                Keep this page open until the workflow completes.
              </p>
            </div>
          </section>
        )}
      </form>
    </div>
  );
}

function PlaceholderPage({ meta }: { meta: PageMeta }) {
  return (
    <div className="page">
      <PageHeader meta={meta} />
      <section className="empty-state">
        <div className="empty-icon">
          <ClipboardPlus size={27} />
        </div>
        <span className="eyebrow">Phase 5 module</span>
        <h2>{meta.title} is next in the build sequence.</h2>
        <p>
          The route and product shell are ready. We will implement this module
          against the existing backend contract instead of filling it with fake
          clinical behavior.
        </p>
      </section>
    </div>
  );
}

function DecisionSupportPage() {
  const location = useLocation();

  const routedResult =
    (
      location.state as
        | { workflowResult?: WorkflowResponse }
        | null
    )?.workflowResult ?? null;

  const [result, setResult] =
    useState<WorkflowResponse | null>(routedResult);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runDemo() {
    setRunning(true);
    setError(null);

    try {
      const response = await runVerifiedSyntheticWorkflow();
      setResult(response);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "The workflow request failed.";
      setError(message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="page">
      <PageHeader meta={pages.decision} />

      <section className="demo-banner">
        <div>
          <span className="eyebrow">Verified engineering path</span>
          <h3>Run the real Docker model workflow from the browser</h3>
          <p>
            The engineering demo now uses the same live assessment preparation
            contract as the clinician-facing workflow. The browser no longer
            constructs model evidence tokens or dense inference features itself.
          </p>
        </div>
        <button
          className="button button-primary workflow-run-button"
          type="button"
          disabled={running}
          onClick={runDemo}
        >
          <Activity size={18} className={running ? "spin" : ""} />
          {running ? "Running model..." : "Run verified model workflow"}
        </button>
      </section>

      {running && (
        <section className="model-progress">
          <Activity size={20} className="spin" />
          <div>
            <strong>XGBoost + local MedGemma are running</strong>
            <p>
              CPU MedGemma inference can take several minutes. Keep this page
              open while the constrained reasoning response is generated.
            </p>
          </div>
        </section>
      )}

      {error && (
        <section className="clinical-error">
          <strong>Workflow request failed</strong>
          <p>{error}</p>
        </section>
      )}

      {result?.workflow_status === "NO_DIFFERENTIAL" && (
        <section className="empty-inline workflow-safe-stop">
          <ShieldCheck size={24} />
          <div>
            <strong>No supported differential returned</strong>
            <p>
              The workflow stopped before downstream reasoning because no
              supported differential candidate was available. Doctor review
              remains required.
            </p>
          </div>
        </section>
      )}

      <section className="decision-grid">
        <div className="panel">
          <span className="eyebrow">Authoritative ranking</span>
          <h3>XGBoost differential candidates</h3>

          {!result ? (
            <div className="empty-inline">
              <Stethoscope size={24} />
              <div>
                <strong>No workflow result yet</strong>
                <p>
                  Run the verified engineering workflow to display the real
                  XGBoost candidates returned by the backend.
                </p>
              </div>
            </div>
          ) : (
            <div className="prediction-list">
              {result.predictions.map((prediction) => (
                <article className="prediction-row" key={prediction.rank}>
                  <div className="rank-badge">{prediction.rank}</div>
                  <div className="prediction-main">
                    <strong>{prediction.disease}</strong>
                    <span>{prediction.confidence} confidence</span>
                  </div>
                  <div className="probability-block">
                    <strong>
                      {(prediction.probability * 100).toFixed(1)}%
                    </strong>
                    <span>model probability</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <span className="eyebrow">Constrained reasoning</span>
          <h3>MedGemma clinical context</h3>

          {!result ? (
            <div className="empty-inline">
              <ShieldCheck size={24} />
              <div>
                <strong>Safety boundary active</strong>
                <p>
                  MedGemma cannot add, remove, re-rank, or change candidate
                  probabilities.
                </p>
              </div>
            </div>
          ) : (
            <div className="reasoning-stack">
              {result.reasoning?.candidate_reasoning.map((candidate) => (
                <article className="reasoning-card" key={candidate.rank}>
                  <div className="reasoning-card-heading">
                    <span>Rank {candidate.rank}</span>
                    <strong>{candidate.disease}</strong>
                  </div>
                  <p>{candidate.rationale}</p>
                </article>
              ))}

              <div className="summary-card">
                <span>Reasoning summary</span>
                <p>
                  {result.reasoning?.reasoning_summary ??
                    "Reasoning unavailable for this workflow result."}
                </p>
              </div>
            </div>
          )}
        </div>
      </section>

      {result && (
        <section className="workflow-meta">
          <div>
            <span>Workflow</span>
            <strong>{result.workflow_status}</strong>
          </div>
          <div>
            <span>Doctor review</span>
            <strong>
              {result.requires_doctor_review ? "Required" : "Not required"}
            </strong>
          </div>
          <div>
            <span>Approval</span>
            <strong>{result.doctor_approval_status}</strong>
          </div>
          <div>
            <span>Workflow ID</span>
            <strong className="workflow-id">{result.workflow_id}</strong>
          </div>
        </section>
      )}

      <section className="clinical-warning">
        <ShieldCheck size={21} />
        <div>
          <strong>Doctor review required</strong>
          <p>
            MedIntel is clinical decision support only. It does not autonomously
            diagnose, prescribe, order medication, or determine disposition.
          </p>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
