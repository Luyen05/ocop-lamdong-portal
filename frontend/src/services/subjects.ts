import http from '@/services/http'
import type {
  AdminSubjectApplication,
  SubjectApplication,
  SubjectApplicationFilters,
  SubjectApplicationListResponse,
  SubjectApplicationPayload,
  SubjectModerationPayload,
} from '@/types/subject'

export async function createSubjectApplication(
  payload: SubjectApplicationPayload,
): Promise<SubjectApplication> {
  const response = await http.post<SubjectApplication>('/subject-applications', payload)
  return response.data
}

export async function getMySubjectApplication(): Promise<SubjectApplication> {
  const response = await http.get<SubjectApplication>('/subject-applications/me')
  return response.data
}

export async function resubmitSubjectApplication(
  payload: SubjectApplicationPayload,
): Promise<SubjectApplication> {
  const response = await http.put<SubjectApplication>('/subject-applications/me', payload)
  return response.data
}

export async function listSubjectApplications(
  filters: SubjectApplicationFilters,
): Promise<SubjectApplicationListResponse> {
  const response = await http.get<SubjectApplicationListResponse>(
    '/admin/subject-applications',
    { params: filters },
  )
  return response.data
}

export async function moderateSubjectApplication(
  applicationId: number,
  payload: SubjectModerationPayload,
): Promise<AdminSubjectApplication> {
  const response = await http.patch<AdminSubjectApplication>(
    `/admin/subject-applications/${applicationId}/moderation`,
    payload,
  )
  return response.data
}
