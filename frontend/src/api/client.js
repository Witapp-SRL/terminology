import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// CodeSystem API
export const codeSystemAPI = {
  list: (params) => client.get('/CodeSystem', { params }),
  get: (id) => client.get(`/CodeSystem/${id}`),
  create: (data) => client.post('/CodeSystem', data),
  update: (id, data) => client.put(`/CodeSystem/${id}`, data),
  delete: (id) => client.delete(`/CodeSystem/${id}`),
  lookup: (params) => client.get('/CodeSystem/$lookup', { params }),
  validateCode: (params) => client.get('/CodeSystem/$validate-code', { params }),
  subsumes: (params) => client.get('/CodeSystem/$subsumes', { params }),
};

// ValueSet API
export const valueSetAPI = {
  list: (params) => client.get('/ValueSet', { params }),
  get: (id) => client.get(`/ValueSet/${id}`),
  create: (data) => client.post('/ValueSet', data),
  update: (id, data) => client.put(`/ValueSet/${id}`, data),
  delete: (id) => client.delete(`/ValueSet/${id}`),
  expand: (params) => client.get('/ValueSet/$expand', { params }),
  expandById: (id, params) => client.get(`/ValueSet/${id}/$expand`, { params }),
  validateCode: (params) => client.get('/ValueSet/$validate-code', { params }),
};

// ConceptMap API
export const conceptMapAPI = {
  list: (params) => client.get('/ConceptMap', { params }),
  get: (id) => client.get(`/ConceptMap/${id}`),
  create: (data) => client.post('/ConceptMap', data),
  update: (id, data) => client.put(`/ConceptMap/${id}`, data),
  delete: (id) => client.delete(`/ConceptMap/${id}`),
  translate: (params) => client.get('/ConceptMap/$translate', { params }),
};

// Metadata API
export const metadataAPI = {
  getCapabilities: () => client.get('/metadata'),
  getTerminologyCapabilities: () => client.get('/metadata?mode=terminology'),
};

export default client;
