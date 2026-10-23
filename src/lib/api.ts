/**
 * API client — connects frontend to FastAPI backend.
 * All calls go through this single configured axios instance.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('apaar_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 → redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('apaar_token');
      localStorage.removeItem('apaar_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/verify') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  demoLogin: (role: string) =>
    api.post('/auth/demo-login', { role }),
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

// ── Institutions ──────────────────────────────────────────────
export const institutionsApi = {
  list: () => api.get('/institutions/'),
  get: (id: string) => api.get(`/institutions/${id}`),
  getSeats: (id: string) => api.get(`/institutions/${id}/seats`),
};

// ── Students ──────────────────────────────────────────────────
export const studentsApi = {
  list: (instId?: string) => api.get('/students/', { params: { institution_id: instId } }),
  get: (id: string) => api.get(`/students/${id}`),
  uploadBatch: (data: any) => api.post('/students/upload-batch', data),
  getSubmissions: (instId: string) => api.get(`/students/institution/${instId}/submissions`),
};

// ── Seats ─────────────────────────────────────────────────────
export const seatsApi = {
  national: () => api.get('/seats/national'),
  institution: (instId: string) => api.get(`/seats/institution/${instId}`),
  all: () => api.get('/seats/all-institutions'),
};

// ── Cases ─────────────────────────────────────────────────────
export const casesApi = {
  list: (params?: any) => api.get('/cases/', { params }),
  get: (id: string) => api.get(`/cases/${id}`),
  decision: (id: string, data: { decision: string; rationale: string }) =>
    api.post(`/cases/${id}/decision`, data),
  assign: (id: string, officerName: string) =>
    api.post(`/cases/${id}/assign`, null, { params: { officer_name: officerName } }),
};

// ── Credentials ──────────────────────────────────────────────
export const credentialsApi = {
  issue: (data: { student_id: string; purpose: string; fields: string[] }) =>
    api.post('/credentials/issue', data),
  verify: (data: { cred_id: string; verifier_name?: string; verifier_id?: string; purpose?: string }) =>
    api.post('/credentials/verify', data),
  revoke: (credId: string) => api.post(`/credentials/${credId}/revoke`),
  accessLog: (studentId: string) => api.get(`/credentials/${studentId}/access-log`),
};

// ── Audit ─────────────────────────────────────────────────────
export const auditApi = {
  events: (chainId?: number) => api.get('/audit/events', { params: { chain_id: chainId } }),
  chains: () => api.get('/audit/chains'),
  append: (data: any) => api.post('/audit/events', null, { params: data }),
  timeMachine: (asOf: string) => api.get('/audit/time-machine', { params: { as_of: asOf } }),
};

// ── Analytics ────────────────────────────────────────────────
export const analyticsApi = {
  overview: () => api.get('/analytics/overview'),
  trustDist: () => api.get('/analytics/trust-distribution'),
  enrolmentTrend: () => api.get('/analytics/enrolment-trend'),
  casesByType: () => api.get('/analytics/cases-by-type'),
  regionWise: () => api.get('/analytics/region-wise'),
  institution: (instId: string) => api.get(`/analytics/institution/${instId}`),
  verifiers: () => api.get('/analytics/verifiers'),
};

// ── Integrity ─────────────────────────────────────────────────
export const integrityApi = {
  rules: () => api.get('/integrity/rules'),
  findings: (instId: string) => api.get(`/integrity/findings/${instId}`),
  rescore: (instId: string) => api.post(`/integrity/rescore/${instId}`),
  trustDist: () => api.get('/integrity/trust-distribution'),
  backtest: (data: { policy_version: number; compare_version: number }) =>
    api.post('/integrity/backtest', data),
};

export { API_BASE };
