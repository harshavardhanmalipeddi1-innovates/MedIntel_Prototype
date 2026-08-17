export type Prediction = {
  rank: number;
  disease: string;
  probability: number;
  confidence: string;
};

export type CandidateReasoning = {
  rank: number;
  disease: string;
  supporting_findings: string[];
  conflicting_findings: string[];
  missing_information: string[];
  rationale: string;
};

export type WorkflowResponse = {
  success: boolean;
  predictions: Prediction[];
  reasoning: {
    candidate_reasoning: CandidateReasoning[];
    important_uncertainties: string[];
    red_flags_to_review: string[];
    next_information_needed: string[];
    reasoning_summary: string;
    limitations: string[];
    requires_doctor_review: boolean;
  } | null;
  verification: {
    suggested_steps: unknown[];
    missing_information_summary: string[];
    requires_doctor_review: boolean;
  } | null;
  treatment_draft: {
    considerations?: unknown[];
    general_cautions: string[];
    status: string;
    requires_doctor_review: boolean;
    doctor_approval_status: string;
  } | null;
  workflow_status: string;
  workflow_id: string;
  requires_doctor_review: boolean;
  doctor_approval_status: string;
};

export type AssessmentOption = {
  value: string;
  label: string;
};

export type AssessmentQuestion = {
  code: string;
  question: string;
  data_type: string;
  answer_kind: string;
  is_antecedent: boolean;
  initial_evidence_allowed: boolean;
  default_value: unknown;
  options: AssessmentOption[];
  scale_min: number | null;
  scale_max: number | null;
};

export type AssessmentQuestionnaire = {
  version: string;
  question_count: number;
  initial_evidence_count: number;
  initial_evidence_codes: string[];
  questions: AssessmentQuestion[];
  source: Record<string, unknown>;
};

export type AssessmentAnswer = {
  code: string;
  value: unknown;
};

export type AssessmentPrepareRequest = {
  age: number;
  sex: "M" | "F";
  initial_evidence: string;
  answers: AssessmentAnswer[];
};

export type AssessmentPrepareResponse = {
  patient_context: Record<string, unknown>;
  initial_evidence: string;
  positive_evidence_tokens: string[];
  answered_question_codes: string[];
  eligible_question_codes: string[];
  answered_question_count: number;
  eligible_question_count: number;
  questionnaire_completion_fraction: number;
};

function decodePossiblyWrappedJson<T>(text: string): T {
  let value: unknown = text.trim();

  for (let depth = 0; depth < 3 && typeof value === "string"; depth += 1) {
    const candidate = value.trim();

    if (!candidate) {
      throw new Error("The backend returned an empty JSON response.");
    }

    try {
      value = JSON.parse(candidate);
    } catch {
      throw new Error("The backend returned an invalid JSON response.");
    }
  }

  if (typeof value === "string") {
    throw new Error("The backend response remained JSON-string wrapped.");
  }

  return value as T;
}

export type ClinicianIdentity = {
  username: string;
  role: "clinician";
};

export type ClinicianTokenResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in_seconds: number;
  clinician: ClinicianIdentity;
};

export type ClinicianSession = {
  access_token: string;
  expires_at: number;
  clinician: ClinicianIdentity;
};

const CLINICIAN_SESSION_KEY = "medintel.clinician.session";
const CLINICIAN_AUTH_EVENT = "medintel-auth-changed";

/*
 * API base URL
 *
 * Development:
 *   VITE_API_BASE_URL=http://127.0.0.1:8000
 *
 * Production:
 *   VITE_API_BASE_URL=https://YOUR-BACKEND-DOMAIN
 *
 * If the variable is empty, requests use the current origin.
 */
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || ""
).replace(/\/+$/, "");

function buildApiUrl(path: string): string {
  if (!path.startsWith("/")) {
    return `${API_BASE_URL}/${path}`;
  }

  return `${API_BASE_URL}${path}`;
}

function emitClinicianAuthChanged(): void {
  window.dispatchEvent(new Event(CLINICIAN_AUTH_EVENT));
}

export function clearClinicianSession(): void {
  window.sessionStorage.removeItem(CLINICIAN_SESSION_KEY);
  emitClinicianAuthChanged();
}

export function getStoredClinicianSession(): ClinicianSession | null {
  const raw = window.sessionStorage.getItem(CLINICIAN_SESSION_KEY);

  if (!raw) {
    return null;
  }

  try {
    const candidate = JSON.parse(raw) as Partial<ClinicianSession>;

    const valid =
      typeof candidate.access_token === "string" &&
      candidate.access_token.length > 0 &&
      typeof candidate.expires_at === "number" &&
      candidate.expires_at > Date.now() &&
      typeof candidate.clinician?.username === "string" &&
      candidate.clinician.username.length > 0 &&
      candidate.clinician.role === "clinician";

    if (valid) {
      return candidate as ClinicianSession;
    }
  } catch {
    // Invalid session data is discarded below.
  }

  clearClinicianSession();
  return null;
}

function storeClinicianSession(session: ClinicianSession): void {
  window.sessionStorage.setItem(
    CLINICIAN_SESSION_KEY,
    JSON.stringify(session),
  );

  emitClinicianAuthChanged();
}

export function subscribeClinicianSession(
  listener: () => void,
): () => void {
  window.addEventListener(
    CLINICIAN_AUTH_EVENT,
    listener,
  );

  return () => {
    window.removeEventListener(
      CLINICIAN_AUTH_EVENT,
      listener,
    );
  };
}

async function requestJson<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs = 30_000,
): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  const clinicianSession = getStoredClinicianSession();

  if (
    clinicianSession &&
    !headers.has("Authorization")
  ) {
    headers.set(
      "Authorization",
      `Bearer ${clinicianSession.access_token}`,
    );
  }

  const url = buildApiUrl(path);

  try {
    const response = await fetch(url, {
      ...init,
      headers,
      signal: controller.signal,
    });

    const body = await response.text();

    if (
      response.status === 401 &&
      path !== "/api/v1/auth/login"
    ) {
      clearClinicianSession();
    }

    if (!response.ok) {
      throw new Error(
        `Request failed (${response.status}): ${
          body || response.statusText
        }`,
      );
    }

    return decodePossiblyWrappedJson<T>(body);
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function loginClinician(
  username: string,
  password: string,
): Promise<ClinicianSession> {
  const response =
    await requestJson<ClinicianTokenResponse>(
      "/api/v1/auth/login",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      },
      30_000,
    );

  const session: ClinicianSession = {
    access_token: response.access_token,
    expires_at:
      Date.now() +
      response.expires_in_seconds * 1000,
    clinician: response.clinician,
  };

  storeClinicianSession(session);

  return session;
}

export async function getCurrentClinician(): Promise<ClinicianIdentity> {
  return requestJson<ClinicianIdentity>(
    "/api/v1/auth/me",
    {
      method: "GET",
    },
    30_000,
  );
}

export async function getAssessmentQuestionnaire(): Promise<AssessmentQuestionnaire> {
  return requestJson<AssessmentQuestionnaire>(
    "/api/v1/clinical/assessment/questionnaire",
    {
      method: "GET",
    },
    30_000,
  );
}

export async function prepareAssessment(
  request: AssessmentPrepareRequest,
): Promise<AssessmentPrepareResponse> {
  return requestJson<AssessmentPrepareResponse>(
    "/api/v1/clinical/assessment/prepare",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
    60_000,
  );
}

export async function runClinicalWorkflow(
  patientContext: Record<string, unknown>,
): Promise<WorkflowResponse> {
  return requestJson<WorkflowResponse>(
    "/api/v1/clinical/workflow",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        patient_context: patientContext,
      }),
    },
    1_300_000,
  );
}

/*
 * Retain the engineering-demo button, but route it through the same
 * AssessmentService contract used by the clinician-facing flow.
 *
 * The browser no longer constructs AGE / evidence_tokens /
 * consultation stage fields itself.
 */
export async function runVerifiedSyntheticWorkflow(): Promise<WorkflowResponse> {
  const questionnaire = await getAssessmentQuestionnaire();

  const initialEvidence = questionnaire.initial_evidence_codes[0];

  if (!initialEvidence) {
    throw new Error(
      "The live assessment questionnaire contains no valid initial evidence.",
    );
  }

  const prepared = await prepareAssessment({
    age: 45,
    sex: "M",
    initial_evidence: initialEvidence,
    answers: [],
  });

  return runClinicalWorkflow(prepared.patient_context);
}