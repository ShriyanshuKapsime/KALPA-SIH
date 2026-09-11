import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:3000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Response interceptor for centralized error formatting
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const customError = {
      message: error.response?.data?.message || error.response?.data?.detail || error.message || 'An unexpected error occurred',
      status: error.response?.status || 500,
      details: error.response?.data?.details || null,
    };
    return Promise.reject(customError);
  }
);

export const apiService = {
  // System Health Checks
  checkGatewayHealth: async () => {
    const res = await axios.get('http://localhost:3000/health');
    return res.data;
  },
  checkAIHealth: async () => {
    return apiClient.get('/health/ai');
  },

  intake: {
    submitVoice: async (formData) => {
      console.log('[FRONTEND → GATEWAY] Submitting voice intake to /intake/voice');
      return apiClient.post('/intake/voice', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
    submitText: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Submitting text intake to /intake/text:', payload);
      return apiClient.post('/intake/text', payload);
    },
    continueIntake: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Submitting continue intake to /intake/continue:', payload);
      return apiClient.post('/intake/continue', payload);
    },
    getSession: async (sessionId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching session /intake/session/${sessionId}`);
      return apiClient.get(`/intake/session/${sessionId}`);
    },
  },

  classification: {
    classify: async (intakeData) => {
      console.log('[FRONTEND → GATEWAY] Submitting classification to /classification/classify:', intakeData);
      return apiClient.post('/classification/classify', intakeData);
    },
    clarify: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Submitting clarification to /classification/clarify:', payload);
      return apiClient.post('/classification/clarify', payload);
    },
    getSession: async (sessionId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching classification /classification/${sessionId}`);
      return apiClient.get(`/classification/${sessionId}`);
    },
    getNICDetails: async (nicCode) => {
      return apiClient.get(`/classification/nic/${nicCode}`);
    },
  },

  profile: {
    buildProfile: async (sessionId) => {
      console.log('[FRONTEND → GATEWAY] Building canonical profile for session:', sessionId);
      return apiClient.post('/profile/build', { session_id: sessionId });
    },
    getProfileByAnalysisId: async (analysisId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching profile /profile/${analysisId}`);
      return apiClient.get(`/profile/${analysisId}`);
    },
    getProfileBySessionId: async (sessionId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching profile /profile/session/${sessionId}`);
      return apiClient.get(`/profile/session/${sessionId}`);
    },
  },

  market: {
    getAnalysis: async (businessId) => apiClient.get(`/market/analysis/${businessId}`),
  },

  feasibility: {
    evaluate: async (businessId) => apiClient.post(`/feasibility/evaluate/${businessId}`),
  },

  dpr: {
    generateReport: async (businessId) => apiClient.post(`/dpr/generate/${businessId}`),
    getReport: async (reportId) => apiClient.get(`/dpr/report/${reportId}`),
  },
};

export default apiService;
