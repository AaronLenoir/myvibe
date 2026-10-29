import axios, { AxiosInstance, AxiosError } from 'axios';
import { User, Team, ShiftType, SchedulePeriod, DayShiftSlot, MemberConstraint, RosterProposal, Assignment, Token, ApiResponse } from '@/types';

// API base URL - will be set from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Add response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse<any>>) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  google: (token: string) => api.post<Token>('/auth/google', { token }),
  facebook: (token: string) => api.post<Token>('/auth/facebook', { token }),
  me: () => api.get<User>('/auth/me'),
  refresh: () => api.post<Token>('/auth/refresh'),
};

// Teams API
export const teamsApi = {
  create: (data: { name: string }) => api.post<Team>('/teams', data),
  list: () => api.get<Team[]>('/teams'),
  get: (id: string) => api.get<Team>(`/teams/${id}`),
  update: (id: string, data: { name?: string }) => api.put<Team>(`/teams/${id}`, data),
  delete: (id: string) => api.delete<void>(`/teams/${id}`),
};

// Users API
export const usersApi = {
  create: (data: any) => api.post<User>('/users', data),
  list: () => api.get<User[]>('/users/team'),
  get: (id: string) => api.get<User>(`/users/${id}`),
  update: (id: string, data: any) => api.put<User>(`/users/${id}`, data),
  delete: (id: string) => api.delete<void>(`/users/${id}`),
  promote: (id: string) => api.post<User>(`/users/${id}/promote`),
};

// Shift Types API
export const shiftTypesApi = {
  create: (data: any) => api.post<ShiftType>('/shift-types', data),
  list: () => api.get<ShiftType[]>('/shift-types'),
  get: (id: string) => api.get<ShiftType>(`/shift-types/${id}`),
  update: (id: string, data: any) => api.put<ShiftType>(`/shift-types/${id}`, data),
  delete: (id: string) => api.delete<void>(`/shift-types/${id}`),
  deactivate: (id: string) => api.post<ShiftType>(`/shift-types/${id}/deactivate`),
};

// Schedule Periods API
export const periodsApi = {
  create: (data: any) => api.post<SchedulePeriod>('/periods', data),
  list: (status?: string) => api.get<SchedulePeriod[]>('/periods', { params: { status } }),
  get: (id: string) => api.get<SchedulePeriod>(`/periods/${id}`),
  getDetails: (id: string) => api.get<SchedulePeriod>(`/periods/${id}/details`),
  update: (id: string, data: any) => api.put<SchedulePeriod>(`/periods/${id}`, data),
  delete: (id: string) => api.delete<void>(`/periods/${id}`),
  advance: (id: string) => api.post<SchedulePeriod>(`/periods/${id}/advance`),
  regress: (id: string) => api.post<SchedulePeriod>(`/periods/${id}/regress`),
  current: () => api.get<SchedulePeriod | null>('/periods/current'),
  upcoming: () => api.get<SchedulePeriod[]>('/periods/upcoming'),
};

// Day Shift Slots API
export const slotsApi = {
  create: (periodId: string, data: any) => api.post<DayShiftSlot>(`/periods/${periodId}/slots`, data),
  list: (periodId: string) => api.get<DayShiftSlot[]>(`/periods/${periodId}/slots`),
  get: (id: string) => api.get<DayShiftSlot>(`/slots/${id}`),
  update: (id: string, data: any) => api.put<DayShiftSlot>(`/slots/${id}`, data),
  delete: (id: string) => api.delete<void>(`/slots/${id}`),
};

// Constraints API
export const constraintsApi = {
  create: (data: any) => api.post<MemberConstraint>('/constraints', data),
  listByPeriod: (periodId: string) => api.get<MemberConstraint[]>(`/constraints/period/${periodId}`),
  listByUser: () => api.get<MemberConstraint[]>('/constraints/user'),
  listByUserAndPeriod: (userId: string, periodId: string) => api.get<MemberConstraint[]>(`/constraints/user/${userId}`, { params: { period_id: periodId } }),
  get: (id: string) => api.get<MemberConstraint>(`/constraints/${id}`),
  update: (id: string, data: any) => api.put<MemberConstraint>(`/constraints/${id}`, data),
  delete: (id: string) => api.delete<void>(`/constraints/${id}`),
  listHard: (periodId: string) => api.get<MemberConstraint[]>(`/constraints/period/${periodId}/hard`),
  listSoft: (periodId: string) => api.get<MemberConstraint[]>(`/constraints/period/${periodId}/soft`),
};

// Proposals API
export const proposalsApi = {
  generate: (periodId: string) => api.post<RosterProposal[]>(`/proposals/generate/${periodId}`),
  list: (periodId: string) => api.get<RosterProposal[]>(`/proposals/period/${periodId}`),
  get: (id: string) => api.get<RosterProposal>(`/proposals/${id}`),
  getSelected: (periodId: string) => api.get<RosterProposal | null>(`/proposals/period/${periodId}/selected`),
  select: (id: string) => api.post<RosterProposal>(`/proposals/${id}/select`),
  listAssignments: (id: string) => api.get<Assignment[]>(`/proposals/${id}/assignments`),
  listViolations: (id: string) => api.get<Violation[]>(`/proposals/${id}/violations`),
  addAssignment: (proposalId: string, data: any) => api.post<Assignment>(`/proposals/${proposalId}/assignments`, data),
  removeAssignment: (id: string) => api.delete<void>(`/proposals/assignments/${id}`),
  validate: (id: string) => api.post<{ valid: boolean; violations: Violation[] }>(`/proposals/${id}/validate`),
  publish: (id: string) => api.post<RosterProposal>(`/proposals/${id}/publish`),
};

// Health check
export const healthApi = {
  check: () => api.get('/health'),
};

export default api;
