import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:3000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Extract string error message from arbitrary API response shapes
function extractErrorMessage(data, fallback = 'An unexpected error occurred') {
  if (!data) return fallback;
  if (typeof data === 'string') return data;

  if (typeof data.message === 'string' && data.message.trim()) {
    return data.message;
  }
  if (typeof data.detail === 'string' && data.detail.trim()) {
    return data.detail;
  }
  if (data.detail && typeof data.detail === 'object' && !Array.isArray(data.detail)) {
    if (typeof data.detail.message === 'string' && data.detail.message.trim()) {
      return data.detail.message;
    }
    if (data.detail.error && typeof data.detail.error === 'object') {
      if (typeof data.detail.error.message === 'string' && data.detail.error.message.trim()) {
        return data.detail.error.message;
      }
    }
    if (typeof data.detail.provider_error === 'string' && data.detail.provider_error.trim()) {
      return data.detail.provider_error;
    }
    if (typeof data.detail.error === 'string' && data.detail.error.trim()) {
      return data.detail.error;
    }
  }
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    const joined = data.detail
      .map((d) => {
        if (!d) return '';
        const loc = Array.isArray(d.loc) ? d.loc.filter((l) => l !== 'body').join('.') : (d.loc || '');
        const msg = d.msg || (typeof d === 'string' ? d : '');
        return loc ? `${loc}: ${msg}` : msg;
      })
      .filter(Boolean)
      .join('; ');
    if (joined.trim()) return joined;
  }
  if (data.error && typeof data.error === 'object') {
    if (typeof data.error.message === 'string' && data.error.message.trim()) {
      return data.error.message;
    }
  }
  if (typeof data.error === 'string' && data.error.trim()) {
    return data.error;
  }
  if (data.details && typeof data.details === 'object') {
    if (typeof data.details.message === 'string') return data.details.message;
    if (typeof data.details.provider_error === 'string') return data.details.provider_error;
  }

  return fallback;
}

// Response interceptor for centralized error formatting
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const resData = error.response?.data;
    const is422 = error.response?.status === 422;
    const customError = {
      message: extractErrorMessage(resData, error.message || 'An unexpected error occurred'),
      status: error.response?.status || 500,
      code: resData?.error?.code || resData?.error || resData?.detail?.error?.code || resData?.detail?.error || (is422 ? 'VALIDATION_ERROR' : 'REQUEST_FAILED'),
      details: resData?.details || resData?.detail?.details || null,
      raw: resData || null,
      validationErrors: is422 && Array.isArray(resData?.detail) ? resData.detail : null,
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

  translate: {
    text: async (text, targetLanguage, sourceLanguage = 'en') => {
      return apiClient.post('/translate/text', { text, target_language: targetLanguage, source_language: sourceLanguage });
    },
    batch: async (texts, targetLanguage, sourceLanguage = 'en') => {
      return apiClient.post('/translate/batch', { texts, target_language: targetLanguage, source_language: sourceLanguage });
    },
    object: async (data, targetLanguage, sourceLanguage = 'en') => {
      return apiClient.post('/translate/object', { data, target_language: targetLanguage, source_language: sourceLanguage });
    },
  },

  intake: {
    submitVoice: async (formData) => {
      console.log('[FRONTEND → GATEWAY] Submitting voice intake to /intake/voice');
      const response = await apiClient.post('/intake/voice', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      if (response && response.success === false) {
        const customErr = {
          message: extractErrorMessage(response, 'Voice processing failed'),
          code: response.error || 'STT_PROCESSING_FAILED',
          status: 400,
          details: response.details || null,
          raw: response
        };
        throw customErr;
      }
      return response;
    },
    transcribe: async (formData) => {
      console.log('[FRONTEND → GATEWAY] Transcribing audio at /intake/transcribe');
      try {
        return await apiClient.post('/intake/transcribe', formData);
      } catch (err) {
        console.warn('[API SERVICE] /intake/transcribe error caught gracefully:', err);
        const errMsg = err?.message || extractErrorMessage(err?.raw, 'Could not detect clear speech in the recording. Please speak closer to the microphone or type your answer.');
        return {
          success: false,
          transcript: null,
          error: err?.code || 'STT_FAILED',
          message: errMsg,
        };
      }
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

  orchestrator: {
    start: async (sessionId, options = {}) => {
      console.log('[FRONTEND → GATEWAY] Starting orchestrator for session:', sessionId);
      return apiClient.post('/orchestrator/start', { session_id: sessionId, ...options });
    },
    getStatus: async (analysisId) => {
      return apiClient.get(`/orchestrator/status/${analysisId}`);
    },
    getById: async (analysisId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching orchestration record /orchestrator/${analysisId}`);
      return apiClient.get(`/orchestrator/${analysisId}`);
    },
    getBySessionId: async (sessionId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching orchestration record /orchestrator/session/${sessionId}`);
      return apiClient.get(`/orchestrator/session/${sessionId}`);
    },
    getWorkflowStatus: async (identifier) => {
      console.log(`[FRONTEND → GATEWAY] Fetching canonical workflow status /orchestrator/workflow/${identifier}`);
      return apiClient.get(`/orchestrator/workflow/${identifier}`);
    },
  },

  knowledge: {
    getCoverageReport: async () => {
      console.log('[FRONTEND → GATEWAY] Fetching knowledge coverage report');
      return apiClient.get('/knowledge/coverage');
    },
    getDataSources: async (params = {}) => {
      return apiClient.get('/knowledge/sources', { params });
    },
    getDataSourceById: async (id) => {
      return apiClient.get(`/knowledge/sources/${encodeURIComponent(id)}`);
    },
    getSchemes: async (params = {}) => {
      return apiClient.get('/knowledge/schemes', { params });
    },
    getSchemeById: async (id) => {
      return apiClient.get(`/knowledge/schemes/${encodeURIComponent(id)}`);
    },
    evaluateSchemeEligibility: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Evaluating scheme eligibility:', payload);
      return apiClient.post('/knowledge/schemes/evaluate', payload);
    },
    getFinancialBenchmarks: async () => {
      return apiClient.get('/knowledge/benchmarks/financial');
    },
    getFinancialBenchmarkById: async (id) => {
      return apiClient.get(`/knowledge/benchmarks/financial/${encodeURIComponent(id)}`);
    },
    getMarketBenchmarks: async () => {
      return apiClient.get('/knowledge/benchmarks/market');
    },
    getMarketBenchmarkById: async (id) => {
      return apiClient.get(`/knowledge/benchmarks/market/${encodeURIComponent(id)}`);
    },
    getBusinessProfiles: async () => {
      return apiClient.get('/knowledge/business-profiles');
    },
    getBusinessProfileById: async (id) => {
      return apiClient.get(`/knowledge/business-profiles/${encodeURIComponent(id)}`);
    },
    getMarketKnowledgePack: async (id, params = {}) => {
      return apiClient.get(`/knowledge/market-pack/${encodeURIComponent(id)}`, { params });
    },
    getFinancialKnowledgePack: async (id, params = {}) => {
      return apiClient.get(`/knowledge/financial-pack/${encodeURIComponent(id)}`, { params });
    },
    calculateFinancialFeasibility: async (payload) => {
      return apiClient.post('/knowledge/financial-pack/calculate', payload);
    },
    getComprehensivePack: async (id, params = {}) => {
      return apiClient.get(`/knowledge/comprehensive-pack/${encodeURIComponent(id)}`, { params });
    },
    getBusinessRequirements: async (id) => {
      return apiClient.get(`/knowledge/business/${encodeURIComponent(id)}/requirements`);
    },
    getBusinessKnowledgePack: async (id, params = {}) => {
      return apiClient.get(`/knowledge/business/${encodeURIComponent(id)}/pack`, { params });
    },
    getRisks: async (params = {}) => {
      return apiClient.get('/knowledge/risks', { params });
    },
    getDocuments: async (params = {}) => {
      return apiClient.get('/knowledge/documents', { params });
    },
    getDynamicRequirements: async (params = {}) => {
      return apiClient.get('/knowledge/dynamic-requirements', { params });
    },
  },

  marketIntelligence: {
    collect: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering market intelligence collection (Stage 5):', payload);
      return apiClient.post('/market-intelligence/collect', payload);
    },
    analyze: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering deterministic market intelligence engine analysis (Stage 6):', payload);
      return apiClient.post('/market-intelligence/analyze', payload);
    },
    getById: async (analysisId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching market evidence /market-intelligence/${analysisId}`);
      return apiClient.get(`/market-intelligence/${analysisId}`);
    },
    getToolHealth: async () => {
      return apiClient.get('/market-intelligence/tools/health');
    },
    retry: async (analysisId, payload = {}) => {
      return apiClient.post(`/market-intelligence/${analysisId}/retry`, payload);
    },
  },

  opportunityEvaluation: {
    analyze: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering deterministic Opportunity Evaluation Engine analysis (Stage 8):', payload);
      return apiClient.post('/opportunity-evaluation/analyze', payload);
    },
    getHealth: async () => {
      console.log('[FRONTEND → GATEWAY] Checking Opportunity Evaluation Engine health');
      return apiClient.get('/opportunity-evaluation/health');
    },
  },

  financialAnalysis: {
    analyze: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering deterministic Financial Engine analysis (Stage 9):', payload);
      return apiClient.post('/financial-analysis/analyze', payload);
    },
    calculate: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering standalone Financial Calculator (Stage 9):', payload);
      return apiClient.post('/financial-analysis/calculator', payload);
    },
    calculator: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering standalone Financial Calculator (Stage 9):', payload);
      return apiClient.post('/financial-analysis/calculator', payload);
    },
    getDprPackage: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Fetching Bankable DPR Financial Package (M6):', payload);
      return apiClient.post('/financial-analysis/dpr-package', payload);
    },
    getHealth: async () => {
      console.log('[FRONTEND → GATEWAY] Checking Financial Engine health');
      return apiClient.get('/financial-analysis/health');
    },
  },


  entrepreneurProfile: {
    analyze: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering deterministic Entrepreneur Profile Engine analysis (Stage 10):', payload);
      return apiClient.post('/entrepreneur-profile/analyze', payload);
    },
    clarify: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Submitting entrepreneur clarification to /entrepreneur-profile/clarify:', payload);
      return apiClient.post('/entrepreneur-profile/clarify', payload);
    },
    getHealth: async () => {
      console.log('[FRONTEND → GATEWAY] Checking Entrepreneur Profile Engine health');
      return apiClient.get('/entrepreneur-profile/health');
    },
  },

  riskAnalysis: {
    analyze: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering deterministic Risk Engine analysis (Stage 11):', payload);
      return apiClient.post('/risk-analysis/analyze', payload);
    },
    getHealth: async () => {
      console.log('[FRONTEND → GATEWAY] Checking Risk Engine health');
      return apiClient.get('/risk-analysis/health');
    },
  },

  market: {
    getAnalysis: async (businessId) => apiClient.get(`/market/analysis/${businessId}`),
  },

  feasibility: {
    analyze: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering Stage 12 Feasibility Engine synthesis:', payload);
      return apiClient.post('/feasibility/analyze', payload);
    },
    getById: async (analysisId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching feasibility record /feasibility/${analysisId}`);
      return apiClient.get(`/feasibility/${analysisId}`);
    },
    getCalculation: async (analysisId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching feasibility calculation trace /feasibility/${analysisId}/calculation`);
      return apiClient.get(`/feasibility/${analysisId}/calculation`);
    },
    getPivotSuggestions: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Fetching pivot suggestions:', payload);
      return apiClient.post('/feasibility/pivot-suggestions', payload);
    },
    getHealth: async () => {
      console.log('[FRONTEND → GATEWAY] Checking Feasibility Engine health');
      return apiClient.get('/feasibility/health');
    },
  },

  swot: {
    analyze: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Triggering Stage 13 Dynamic SWOT Agent:', payload);
      return apiClient.post('/swot/analyze', payload, { timeout: 120000 });
    },
    stream: async (payload, onEvent) => {
      console.log('[FRONTEND → GATEWAY] Starting Stage 13 SWOT Stream:', payload);
      const url = `${API_BASE_URL}/swot/stream`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errDetails = '';
        try {
          const errJson = await response.json();
          errDetails = errJson.message || errJson.error || JSON.stringify(errJson);
        } catch {
          errDetails = await response.text();
        }
        throw new Error(`SWOT Stream failed (${response.status}): ${errDetails}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim();
            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                if (onEvent) onEvent(parsed);
              } catch (e) {
                console.warn('[SWOT STREAM] Failed to parse event JSON:', dataStr, e);
              }
            }
          }
        }
      }
    },
    getById: async (analysisId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching SWOT record /swot/${analysisId}`);
      return apiClient.get(`/swot/${analysisId}`);
    },
    getHealth: async () => {
      console.log('[FRONTEND → GATEWAY] Checking SWOT Agent health');
      return apiClient.get('/swot/health');
    },
  },

  assistant: {
    health: async () => {
      console.log('[FRONTEND → GATEWAY] Checking assistant health');
      return apiClient.get('/assistant/health');
    },
    chat: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Sending assistant chat message:', payload);
      return apiClient.post('/assistant/chat', payload, { timeout: 95000 });
    },
    stt: async (formData) => {
      console.log('[FRONTEND → GATEWAY] Sending assistant voice audio for STT (Saaras v4)');
      return apiClient.post('/assistant/stt', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 45000,
      });
    },
    tts: async (payload) => {
      console.log('[FRONTEND → GATEWAY] Requesting assistant voice synthesis for TTS (Bulbul v3):', payload?.language);
      return apiClient.post('/assistant/tts', payload, { timeout: 45000 });
    },
    getHistory: async (targetId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching assistant history for: ${targetId}`);
      return apiClient.get(`/assistant/${targetId}/history`);
    },
    getContext: async (targetId) => {
      console.log(`[FRONTEND → GATEWAY] Fetching assistant context for: ${targetId}`);
      return apiClient.get(`/assistant/${targetId}/context`);
    },
    clearHistory: async (targetId) => {
      console.log(`[FRONTEND → GATEWAY] Clearing assistant history for: ${targetId}`);
      return apiClient.delete(`/assistant/${targetId}/history`);
    },
  },

  dpr: {
    getContext: async (businessId, params = {}) => apiClient.get(`/dpr/context/${businessId}`, { params }),
    getGapAnalysis: async (businessId, params = {}) => apiClient.get(`/dpr/gap-analysis/${businessId}`, { params }),
    getSections: async (businessId, params = {}) => apiClient.get(`/dpr/sections/${businessId}`, { params }),
    getAssumptions: async (businessId, params = {}) => apiClient.get(`/dpr/assumptions/${businessId}`, { params }),
    getNextQuestion: async (businessId, params = {}) => apiClient.get(`/dpr/question/next/${businessId}`, { params }),
    answerQuestion: async (businessId, payload) => apiClient.post(`/dpr/question/answer/${businessId}`, payload),
    setOverride: async (businessId, payload) => apiClient.post(`/dpr/override/${businessId}`, payload),
    acceptBenchmark: async (businessId, payload) => apiClient.post(`/dpr/benchmark/accept/${businessId}`, payload),
    updateDocument: async (businessId, payload) => apiClient.post(`/dpr/document/update/${businessId}`, payload),
    recalculate: async (businessId, params = {}) => apiClient.post(`/dpr/recalculate/${businessId}`, null, { params }),
    getReadiness: async (businessId, params = {}) => apiClient.get(`/dpr/readiness/${businessId}`, { params }),
    getPackage: async (businessId, params = {}) => apiClient.get(`/dpr/package/${businessId}`, { params }),
    getHandoff: async (businessId, params = {}) => apiClient.get(`/dpr/handoff/${businessId}`, { params }),
    submitIntake: async (businessId, payload) => apiClient.post(`/dpr/intake/${businessId}`, payload),
    getDebugLineage: async (businessId, params = {}) => apiClient.get(`/dpr/stage1/debug/lineage/${businessId}`, { params }),
    // Explicit New Scenario Creation
    createNewScenario: async (businessId, payload = {}) => apiClient.post(`/dpr/new-scenario/${businessId}`, payload),
    // Stage 14.2: DPR Enrichment & Deterministic Inference
    getEnrichment: async (businessId, params = {}) => apiClient.get(`/dpr/14.2/enrichment/${businessId}`, { params }),
    runEnrichment: async (businessId, payload = {}, params = {}) => apiClient.post(`/dpr/enrichment/run/${businessId}`, payload, { params }),
    // Dev tools
    resetScenario: async (payload) => apiClient.post('/dpr/dev/reset-scenario', payload),
    getFieldLineage: async (businessId, scenarioId, fieldId) => apiClient.get(`/dpr/debug/field-lineage/${businessId}/${scenarioId}/${fieldId}`),
    getEnrichmentAssumptions: async (businessId, params = {}) => apiClient.get(`/dpr/enrichment/assumptions/${businessId}`, { params }),
    updateEnrichmentAssumption: async (businessId, payload, params = {}) => apiClient.post(`/dpr/14.2/assumption/${businessId}`, payload, { params }),
    getEnrichmentStatus: async (businessId, params = {}) => apiClient.get(`/dpr/enrichment/status/${businessId}`, { params }),
    get14_2Context: async (businessId, params = {}) => apiClient.get(`/dpr/14.2/context/${businessId}`, { params }),
    get14_2Gaps: async (businessId, params = {}) => apiClient.get(`/dpr/14.2/gaps/${businessId}`, { params }),
    answer14_2Question: async (businessId, payload) => apiClient.post(`/dpr/14.2/answer/${businessId}`, payload),
    accept14_2Benchmark: async (businessId, payload) => apiClient.post(`/dpr/14.2/benchmark/accept/${businessId}`, payload),
    update14_2Document: async (businessId, payload) => apiClient.post(`/dpr/14.2/document/${businessId}`, payload),
    get14_2Validation: async (businessId, params = {}) => apiClient.get(`/dpr/14.2/validation/${businessId}`, { params }),
    get14_2Readiness: async (businessId, params = {}) => apiClient.get(`/dpr/14.2/readiness/${businessId}`, { params }),
    transcribeAudio: async (formData, language = 'en') => {
      const baseUrl = (apiClient.defaults?.baseURL || API_BASE_URL || 'http://localhost:3000/api').replace(/\/+$/, '');
      const url = `${baseUrl}/dpr/audio/transcribe?language_code=${encodeURIComponent(language)}`;
      const res = await fetch(url, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.message || errData?.detail || `Transcription failed with status ${res.status}`);
      }
      const data = await res.json();
      return { data };
    },
    synthesizeAudio: async (payload) => apiClient.post('/dpr/audio/synthesize', payload),
    generateReport: async (businessId, payload = {}) => apiClient.post(`/dpr/generate/${businessId}`, payload),
    getReport: async (reportId) => apiClient.get(`/dpr/report/${reportId}`),
    downloadPdfUrl: (reportId) => `${apiClient.defaults?.baseURL || '/api'}/dpr/report/${reportId}/pdf`,
    // Stage 14.3: Final DPR Generation & PDF Engine
    generate14_3DPR: async (businessId, payload = {}) => apiClient.post(`/dpr/14.3/generate/${businessId}`, payload),
    get14_3Status: async (documentId) => apiClient.get(`/dpr/14.3/status/${documentId}`),
    preview14_3Url: (documentId) => `${apiClient.defaults?.baseURL || '/api'}/dpr/14.3/preview/${documentId}`,
    download14_3Url: (documentId) => `${apiClient.defaults?.baseURL || '/api'}/dpr/14.3/download/${documentId}`,
  },
};



export default apiService;
