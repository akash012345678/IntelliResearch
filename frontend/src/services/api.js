import axios from 'axios';

// Base URL points to the local FastAPI backend server
const API_BASE_URL = 'http://localhost:8000/api';

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
};

export default apiClient;
