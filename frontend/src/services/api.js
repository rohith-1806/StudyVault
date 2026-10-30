const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export const getToken = () => localStorage.getItem('studyvault_token');
export const setToken = (token) => localStorage.setItem('studyvault_token', token);
export const removeToken = () => localStorage.removeItem('studyvault_token');

async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
    'Bypass-Tunnel-Reminder': 'true',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, config);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(data.error || `Request failed with status ${response.status}`);
    error.status = response.status;
    error.code = data.code;
    error.data = data;
    throw error;
  }

  return data;
}

export const api = {
  // Auth
  register: (payload) => request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  getMe: () => request('/auth/me'),
  logout: () => request('/auth/logout', { method: 'POST' }),

  // Documents
  getDocuments: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/documents?${query}`);
  },
  getDocument: (id) => request(`/documents/${id}`),
  recordView: (id) => request(`/documents/${id}/view`, { method: 'POST' }),
  uploadDocument: (formData) => request('/documents/upload', { method: 'POST', body: formData }),
  downloadDocument: async (id) => {
    const token = getToken();
    const headers = {
      'Bypass-Tunnel-Reminder': 'true',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}/documents/${id}/download`, {
      method: 'GET',
      headers,
    });

    const contentType = response.headers.get('content-type') || '';

    if (!response.ok) {
      let errData = {};
      try {
        errData = await response.json();
      } catch (e) {
        errData = { error: `Request failed with status ${response.status}` };
      }
      const error = new Error(errData.error || `Download failed with status ${response.status}`);
      error.status = response.status;
      error.code = errData.code;
      error.data = errData;
      throw error;
    }

    if (contentType.includes('application/json')) {
      const data = await response.json();
      return { type: 'url', ...data };
    }

    const blob = await response.blob();
    let fileName = `document-${id}.pdf`;
    const disposition = response.headers.get('content-disposition');
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (match && match[1]) {
        fileName = match[1].replace(/['"]/g, '').trim();
      }
    }
    return { type: 'blob', blob, fileName };
  },
  deleteDocument: (id) => request(`/documents/${id}`, { method: 'DELETE' }),
  reportDocument: (id, payload) => request(`/documents/${id}/report`, { method: 'POST', body: JSON.stringify(payload) }),
  getStreamUrl: (id) => `${API_BASE}/documents/${id}/stream`,
  summarizeDocument: (id, refresh = false) => request(`/documents/${id}/summarize${refresh ? '?refresh=true' : ''}`, { method: 'POST' }),
  getCachedSummary: (id) => request(`/documents/${id}/summary`),

  // Profile
  getProfile: () => request('/profile'),
  getContributions: () => request('/profile/contributions'),

  // Admin
  adminLogin: (payload) => request('/admin/login', { method: 'POST', body: JSON.stringify(payload) }),
  getAdminDashboard: () => request('/admin/dashboard'),
  getPendingDocuments: () => request('/admin/documents/pending'),
  approveDocument: (id) => request(`/admin/documents/${id}/approve`, { method: 'PATCH' }),
  rejectDocument: (id, payload) => request(`/admin/documents/${id}/reject`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteDocumentAdmin: (id) => request(`/admin/documents/${id}`, { method: 'DELETE' }),
  getAdminUsers: () => request('/admin/users'),
  toggleUserStatus: (id, is_active) => request(`/admin/users/${id}/status`, { method: 'PATCH', body: JSON.stringify({ is_active }) }),
  getAdminReports: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/admin/reports?${query}`);
  },
  resolveReport: (id, status) => request(`/admin/reports/${id}/resolve`, { method: 'PATCH', body: JSON.stringify({ status }) })
};
