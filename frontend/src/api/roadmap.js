import axios from 'axios';

const REQUEST_TIMEOUT_MS = 30_000;
const api = axios.create({ headers: { 'Content-Type': 'application/json' }, timeout: REQUEST_TIMEOUT_MS });

export class RoadmapApiError extends Error {
  constructor(message, { code = 'REQUEST_FAILED', requestId, status } = {}) {
    super(message);
    this.name = 'RoadmapApiError';
    this.code = code;
    this.requestId = requestId;
    this.status = status;
  }
}

function getApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (!configuredUrl || configuredUrl.includes('[') || configuredUrl.includes(']')) {
    throw new RoadmapApiError('Roadmap service is not configured. Please contact support.', { code: 'API_NOT_CONFIGURED' });
  }
  try {
    return new URL(configuredUrl).toString().replace(/\/$/, '');
  } catch {
    throw new RoadmapApiError('Roadmap service is not configured. Please contact support.', { code: 'API_NOT_CONFIGURED' });
  }
}

function createRequestId() {
  return globalThis.crypto?.randomUUID?.() || `roadmap-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toRoadmapError(error, requestId) {
  if (error instanceof RoadmapApiError) return error;
  const status = error.response?.status;
  const serverMessage = error.response?.data?.message;
  if (error.code === 'ERR_CANCELED') return new RoadmapApiError('The roadmap request was cancelled. Please retry.', { code: 'CANCELLED', requestId });
  if (error.code === 'ECONNABORTED') return new RoadmapApiError('The roadmap service took too long to respond. Please retry.', { code: 'TIMEOUT', requestId });
  if (status === 400) return new RoadmapApiError(serverMessage || 'Please check your roadmap details and try again.', { code: 'INVALID_REQUEST', requestId, status });
  if (status === 401) return new RoadmapApiError('Your session has expired. Please sign in again.', { code: 'UNAUTHORIZED', requestId, status });
  if (status === 404) return new RoadmapApiError('The roadmap service is unavailable. Please try again later.', { code: 'NOT_FOUND', requestId, status });
  if (status >= 500) return new RoadmapApiError('The roadmap service is temporarily unavailable. Please retry shortly.', { code: 'SERVER_ERROR', requestId, status });
  return new RoadmapApiError('Unable to reach the roadmap service. Check your connection and retry.', { code: 'NETWORK_ERROR', requestId, status });
}

/** Response contract consumed by the existing roadmap UI and required from the backend. */
function validateRoadmapResponse(data, requestId) {
  const validModules = Array.isArray(data?.learning_modules) && data.learning_modules.every((module) =>
    typeof module?.title === 'string'
    && Array.isArray(module?.tasks)
    && module.tasks.every((task) => typeof task?.task_id === 'string' && typeof task?.title === 'string' && typeof task?.is_completed === 'boolean')
  );
  if (!Number.isFinite(data?.match_score) || !Array.isArray(data?.missing_skills) || !validModules) {
    throw new RoadmapApiError('The roadmap service returned an invalid response. Please retry.', { code: 'INVALID_RESPONSE', requestId });
  }
  return data;
}

async function postRoadmap(path, payload, { signal } = {}) {
  const requestId = createRequestId();
  try {
    const { data } = await api.post(path, payload, {
      baseURL: getApiBaseUrl(), signal, headers: { 'X-Request-ID': requestId },
    });
    return validateRoadmapResponse(data, requestId);
  } catch (error) {
    const roadmapError = toRoadmapError(error, requestId);
    console.error('[roadmap-api]', { path, requestId, status: roadmapError.status, code: roadmapError.code });
    throw roadmapError;
  }
}

export function generateRoadmap({ currentSkills, targetType, targetValue, resume }, options) {
  return postRoadmap('/api/generate-roadmap', {
    current_skills: currentSkills,
    target_type: targetType,
    target_value: targetValue,
    resume: resume ? { name: resume.name, type: resume.type, size: resume.size } : null,
  }, options);
}

export function refineRoadmap({ currentRoadmap, prompt }, options) {
  return postRoadmap('/api/refine-roadmap', { current_roadmap: currentRoadmap, prompt }, options);
}

export async function updateTaskProgress({ taskId, isCompleted }) {
  const requestId = createRequestId();
  try {
    const { data } = await api.patch('/api/roadmap/update-progress', {
      task_id: taskId, is_completed: isCompleted,
    }, { baseURL: getApiBaseUrl(), headers: { 'X-Request-ID': requestId } });
    return data;
  } catch (error) {
    const roadmapError = toRoadmapError(error, requestId);
    console.error('[roadmap-api]', { path: '/api/roadmap/update-progress', requestId, status: roadmapError.status, code: roadmapError.code });
    throw roadmapError;
  }
}
