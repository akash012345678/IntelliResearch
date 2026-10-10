import axios from 'axios';

// Base URL points to the configured API URL or defaults to localhost FastAPI backend server
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  /**
   * Upload a research paper PDF with progress monitoring.
   */
  uploadPaper: (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      },
    });
  },

  /**
   * Fetch all papers, optionally filtering by title.
   */
  getPapers: (title = '') => {
    const url = title ? `/papers?title=${encodeURIComponent(title)}` : '/papers';
    return apiClient.get(url);
  },

  /**
   * Fetch details of a single paper by its ID.
   */
  getPaper: (id) => {
    return apiClient.get(`/paper/${id}`);
  },

  /**
   * Delete a paper by its ID.
   */
  deletePaper: (id) => {
    return apiClient.delete(`/paper/${id}`);
  },

  /**
   * Perform semantic similarity search using natural language query.
   */
  semanticSearch: (query, top_k = 5) => {
    return apiClient.post('/semantic/search', { query, top_k });
  },

  /**
   * Fetch semantically related papers for a given paper ID.
   */
  getRelatedPapers: (paperId, top_k = 5) => {
    return apiClient.get(`/semantic/papers/${paperId}/related?top_k=${top_k}`);
  },

  /**
   * Fetch Knowledge Graph nodes, edges, and statistics (with optional type filter).
   */
  getKnowledgeGraph: (type = '') => {
    const url = type ? `/knowledge-graph?type=${encodeURIComponent(type)}` : '/knowledge-graph';
    return apiClient.get(url);
  },

  /**
   * Fetch Knowledge Graph statistics object directly.
   */
  getKnowledgeGraphStatistics: () => {
    return apiClient.get('/knowledge-graph/statistics');
  },

  /**
   * Fetch top connected research entities by actual Knowledge Graph connectivity.
   */
  getTopGraphEntities: (top_k = 5) => {
    return apiClient.get(`/knowledge-graph/top-entities?top_k=${top_k}`);
  },

  /**
   * Fetch Global Research Intelligence analysis across the entire indexed collection.
   */
  getResearchIntelligence: (params = {}) => {
    return apiClient.get('/research-intelligence', { params });
  },

  /**
   * Alias method for fetching Global Research Analysis across the entire collection.
   */
  getResearchAnalysis: (params = {}) => {
    return apiClient.get('/research-intelligence', { params });
  },

  /**
   * Fetch Actionable Research Directions synthesized from multi-signal collection evidence.
   */
  getResearchDirections: (top_k = 10) => {
    return apiClient.get(`/research-directions?top_k=${top_k}`);
  },

  /**
   * Export Actionable Research Directions in Markdown, JSON, or PDF format as a downloadable blob.
   */
  exportResearchDirections: (format = 'md', top_k = 10) => {
    return apiClient.get(`/research-directions/export?format=${encodeURIComponent(format)}&top_k=${top_k}`, {
      responseType: 'blob',
    });
  },

  /**
   * Synthesize a structured academic research proposal draft from a research direction ID.
   */
  generateProposalDraft: (payloadOrDirectionId, optionalProjectId = null) => {
    let body;
    if (typeof payloadOrDirectionId === 'string') {
      body = { direction_id: payloadOrDirectionId };
      if (optionalProjectId) {
        body.project_id = parseInt(optionalProjectId, 10);
      }
    } else {
      body = payloadOrDirectionId;
    }
    return apiClient.post('/research-directions/draft', body);
  },

  // =========================================================================
  // PHASE 6 PART 1 — RESEARCH PROJECTS & PERSISTENCE APIs
  // =========================================================================

  createProject: (data) => apiClient.post('/projects', data),
  getProjects: () => apiClient.get('/projects'),
  getResearchProjects: () => apiClient.get('/projects'),
  getProject: (projectId) => apiClient.get(`/projects/${projectId}`),
  updateProject: (projectId, data) => apiClient.patch(`/projects/${projectId}`, data),
  deleteProject: (projectId) => apiClient.delete(`/projects/${projectId}`),

  addPaperToProject: (projectId, paperId) => apiClient.post(`/projects/${projectId}/papers/${paperId}`),
  bulkAddPapersToProject: (projectId, paperIds) => apiClient.post(`/projects/${projectId}/papers/bulk`, { paper_ids: paperIds }),
  removePaperFromProject: (projectId, paperId) => apiClient.delete(`/projects/${projectId}/papers/${paperId}`),
  getProjectPapers: (projectId) => apiClient.get(`/projects/${projectId}/papers`),
  getAvailableProjectPapers: (projectId, params = {}) => apiClient.get(`/projects/${projectId}/available-papers`, { params }),


  saveDirection: (projectId, data) => apiClient.post(`/projects/${projectId}/directions`, data),
  getProjectDirections: (projectId) => apiClient.get(`/projects/${projectId}/directions`),
  deleteDirection: (projectId, directionId) => apiClient.delete(`/projects/${projectId}/directions/${directionId}`),

  saveProposal: (data) => apiClient.post('/proposals', data),
  getProposal: (proposalId) => apiClient.get(`/proposals/${proposalId}`),
  getProjectProposals: (projectId) => apiClient.get(`/projects/${projectId}/proposals`),
  deleteProposal: (proposalId) => apiClient.delete(`/proposals/${proposalId}`),
  getProposalVersions: (proposalId) => apiClient.get(`/proposals/${proposalId}/versions`),
  getProposalVersion: (proposalId, versionNumber) => apiClient.get(`/proposals/${proposalId}/versions/${versionNumber}`),
  updateProposal: (proposalId, data) => apiClient.patch(`/proposals/${proposalId}`, data),
  compareProposalVersions: (proposalId, versionA, versionB) => apiClient.get(`/proposals/${proposalId}/compare?version_a=${versionA}&version_b=${versionB}`),
  restoreProposalVersion: (proposalId, versionNumber) => apiClient.post(`/proposals/${proposalId}/restore/${versionNumber}`),
  exportProposal: (proposalId, format = 'markdown', versionNumber = null) => apiClient.get(`/proposals/${proposalId}/export?format=${encodeURIComponent(format)}${versionNumber ? `&version_number=${versionNumber}` : ''}`, { responseType: 'blob' }),
  exportRawProposal: (payload, format = 'markdown', versionNumber = 1) => apiClient.post(`/proposals/export?format=${encodeURIComponent(format)}&version_number=${versionNumber}`, payload, { responseType: 'blob' }),
  getProjectResearchIntelligence: (projectId, params) => apiClient.get(`/projects/${projectId}/research-intelligence`, { params }),
  reindexProject: (projectId) => apiClient.post(`/projects/${projectId}/reindex`),
  getProjectResearchReport: (projectId, params) => apiClient.get(`/projects/${projectId}/research-report`, { params }),
  getProjectTraceability: (projectId) => apiClient.get(`/projects/${projectId}/traceability`),
  exportProjectResearchReport: (projectId, format, params) => apiClient.get(`/projects/${projectId}/research-report/export`, {
    params: { format, ...params },
    responseType: format === 'json' ? 'json' : 'blob'
  }),

  // PHASE 7 PART 2 — OPPORTUNITY EVALUATION APIs
  evaluateOpportunity: (directionId) => apiClient.get(`/research-directions/${directionId}/evaluate`),
  evaluateProjectOpportunity: (projectId, directionId) => apiClient.get(`/projects/${projectId}/research-directions/${directionId}/evaluate`),

  // PHASE 7 PART 3 — OPPORTUNITY VALIDATION & LITERATURE SEARCH APIs
  validateOpportunity: (directionId) => apiClient.get(`/research-directions/${directionId}/validate`),
  validateProjectOpportunity: (projectId, directionId) => apiClient.get(`/projects/${projectId}/research-directions/${directionId}/validate`),
  searchLiterature: (query, top_k = 5) => apiClient.post('/research-directions/literature-search', { query, top_k }),

  // PHASE 7 PART 4 — RESEARCH METHODOLOGY & EXPERIMENT PLANNER APIs
  getMethodologyPlan: (directionId) => apiClient.get(`/research-directions/${directionId}/methodology-plan`),
  getProjectMethodologyPlan: (projectId, directionId) => apiClient.get(`/projects/${projectId}/research-directions/${directionId}/methodology-plan`),
  saveProjectResearchPlan: (projectId, directionId, plan_data, notes) => apiClient.post(`/projects/${projectId}/research-plan/save`, { direction_id: directionId, plan_data, notes }),

  // PHASE 7 PART 5 — RESEARCH EXPERIMENT WORKSPACE & RESULT TRACKING APIs
  getProjectExperiments: (projectId) => apiClient.get(`/projects/${projectId}/experiments`),
  getExperimentSummary: (projectId) => apiClient.get(`/projects/${projectId}/experiments/summary`),
  createProjectExperiment: (projectId, payload) => apiClient.post(`/projects/${projectId}/experiments`, payload),
  importMethodologyExperiments: (projectId, directionId) => apiClient.post(`/projects/${projectId}/experiments/import-plan`, { direction_id: directionId }),
  getProjectExperimentDetail: (projectId, experimentId) => apiClient.get(`/projects/${projectId}/experiments/${experimentId}`),
  updateProjectExperiment: (projectId, experimentId, payload) => apiClient.patch(`/projects/${projectId}/experiments/${experimentId}`, payload),
  deleteProjectExperiment: (projectId, experimentId) => apiClient.delete(`/projects/${projectId}/experiments/${experimentId}`),
  createExperimentRun: (projectId, experimentId, payload) => apiClient.post(`/projects/${projectId}/experiments/${experimentId}/runs`, payload),
  recordExperimentResults: (projectId, runId, resultsPayload) => apiClient.post(`/projects/${projectId}/experiments/runs/${runId}/results`, resultsPayload),

  // PHASE 7 PART 6 — RESEARCH RESULTS ANALYSIS & EVIDENCE-BASED CONCLUSION ENGINE APIs
  getProjectResultsAnalysis: (projectId, directionId = null) => apiClient.get(`/projects/${projectId}/results-analysis${directionId ? `?direction_id=${encodeURIComponent(directionId)}` : ''}`),
  getSingleExperimentAnalysis: (projectId, experimentId) => apiClient.get(`/projects/${projectId}/experiments/${experimentId}/results-analysis`),
  getProjectSafeConclusion: (projectId) => apiClient.get(`/projects/${projectId}/results-analysis/conclusion`),

  // PHASE 7 PART 7 — UNIFIED STUDENT RESEARCH JOURNEY APIs
  getProjectResearchJourney: (projectId) => apiClient.get(`/projects/${projectId}/research-journey`),

  // PHASE 8 PART 1 — EVIDENCE-GROUNDED RESEARCH PAPER / THESIS GENERATOR APIs
  getProjectManuscript: (projectId) => apiClient.get(`/projects/${projectId}/academic-manuscript`),
  generateProjectManuscript: (projectId) => apiClient.post(`/projects/${projectId}/academic-manuscript/generate`),
  saveManuscriptVersion: (projectId, payload) => apiClient.post(`/projects/${projectId}/academic-manuscript/versions`, payload),
  getManuscriptVersions: (projectId) => apiClient.get(`/projects/${projectId}/academic-manuscript/versions`),
  restoreManuscriptVersion: (projectId, versionNumber) => apiClient.post(`/projects/${projectId}/academic-manuscript/versions/${versionNumber}/restore`),
  compareManuscriptVersions: (projectId, v1, v2) => apiClient.get(`/projects/${projectId}/academic-manuscript/versions/compare?v1=${v1}&v2=${v2}`),
  exportManuscript: (projectId, format = 'markdown') => {
    if (format === 'pdf' || format === 'docx') {
      return apiClient.get(`/projects/${projectId}/academic-manuscript/export?format=${format}`, { responseType: 'blob' });
    }
    return apiClient.get(`/projects/${projectId}/academic-manuscript/export?format=${format}`);
  },

  // PHASE 8 PART 2 — ACADEMIC PAPER QUALITY, CITATION INTELLIGENCE & REFERENCE MANAGEMENT APIs
  getManuscriptCitations: (projectId) => apiClient.get(`/projects/${projectId}/academic-manuscript/citations`),
  getManuscriptQuality: (projectId) => apiClient.get(`/projects/${projectId}/academic-manuscript/quality`),
  validateManuscriptText: (projectId) => apiClient.post(`/projects/${projectId}/academic-manuscript/validate`),

  // PHASE 8 PART 3 — ACADEMIC DOCUMENT FORMATTING, FIGURES, TABLES & SUBMISSION PACKAGE APIs
  validateAcademicDocument: (projectId) => apiClient.get(`/projects/${projectId}/academic-document/validate`),
  getDocumentPreview: (projectId, config) => apiClient.post(`/projects/${projectId}/academic-document/preview`, config),
  downloadSubmissionPackage: (projectId) => apiClient.get(`/projects/${projectId}/submission-package`, { responseType: 'blob' }),

  // PHASE 8 PART 4 — FINAL STUDENT RESEARCH DASHBOARD AGGREGATE API
  getProjectDashboardAggregate: (projectId) => apiClient.get(`/projects/${projectId}/research-dashboard`),
};



export default apiClient;



