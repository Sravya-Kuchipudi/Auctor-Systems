/**
 * Auctor Systems — API Client
 * Connects React frontend directly to FastAPI backend endpoints.
 */

const API_BASE = '/api';

/**
 * Handle API responses with clear error extraction
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' 
          ? errorJson.detail 
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // response was not json
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  /**
   * Check backend health and configuration
   */
  async getHealth() {
    return request('/health');
  },

  /**
   * Get supported deployment providers
   */
  async getProviders() {
    return request('/deployment/providers');
  },

  /**
   * Start generating a website from user prompt
   * Returns { project_id, status, message }
   */
  async generateProject(prompt, mode = 'real') {
    return request('/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt, mode }),
    });
  },

  /**
   * Submit human clarification answer to resume Beatrice Stone and the workflow
   */
  async submitClarification(projectId, answer) {
    return request(`/project/${projectId}/clarification`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  },

  /**
   * Get complete project state (agents, files, outputs)
   */
  async getProject(projectId) {
    return request(`/project/${projectId}`);
  },

  /**
   * Get list of generated source and doc files
   */
  async getProjectFiles(projectId) {
    return request(`/project/${projectId}/files`);
  },

  /**
   * Get raw content of a specific file
   */
  async getFileContent(projectId, filename) {
    const res = await fetch(`${API_BASE}/project/${projectId}/files/${filename}`);
    if (!res.ok) throw new Error(`Failed to load file ${filename}`);
    return res.text();
  },

  /**
   * URL for rendering the live HTML site in an iframe
   */
  getPreviewUrl(projectId) {
    return `${API_BASE}/project/${projectId}/preview`;
  },

  /**
   * URL for downloading the production ZIP package
   */
  getExportUrl(projectId) {
    return `${API_BASE}/project/${projectId}/export`;
  },

  /**
   * List all saved projects from SQLite
   */
  async listProjects() {
    const data = await request('/projects');
    return Array.isArray(data) ? data : (data.projects || []);
  },

  /**
   * Update project metadata (name, description, prompt)
   */
  async updateProject(projectId, updateData) {
    return request(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  },

  /**
   * Delete a project from SQLite and disk
   */
  async deleteProject(projectId) {
    return request(`/projects/${projectId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get chronological activity history for a project
   */
  async getProjectActivities(projectId) {
    return request(`/projects/${projectId}/activities`);
  },

  /**
   * Modify an existing project via targeted revision directive (Phase 4B)
   */
  async modifyProject(projectId, prompt, mode = 'real') {
    return request(`/project/${projectId}/modify`, {
      method: 'POST',
      body: JSON.stringify({ prompt, mode }),
    });
  },

  /**
   * Get historical revision records for a project
   */
  async getProjectRevisions(projectId) {
    return request(`/project/${projectId}/revisions`);
  },

  /**
   * Rollback project to verified historical revision snapshot (Phase 4C Stage 1)
   */
  async rollbackRevision(projectId, targetRevision) {
    return request(`/project/${projectId}/rollback`, {
      method: 'POST',
      body: JSON.stringify({ target_revision: targetRevision }),
    });
  },

  /**
   * Deploy to provider (e.g. 'vercel')
   */
  async deployProject(projectId, provider = 'vercel') {
    return request(`/project/${projectId}/deploy?provider=${encodeURIComponent(provider)}`, {
      method: 'POST',
    });
  },
};

