import { apiOptional, apiRequest, storeAuthToken, storeStepUpToken } from "./http";
import type {
  AgentCredentialRecord,
  AgentCredentialResponse,
  AccountExportResponse,
  AccountRequestRecord,
  AuthOrganization,
  AuthOrganizationDetail,
  AuthOrganizationInvite,
  AuthOrganizationRole,
  AuthSessionResponse,
  AuthSessionRecord,
  AuthUser,
  LoginResponse,
  MfaSetupResponse,
  StepUpResponse,
  StepUpPurpose,
} from "../types/auth";

const jsonHeaders = { "Content-Type": "application/json" };

export interface RegisterPayload {
  email: string;
  password: string;
  display_name?: string | null;
  whatsapp?: string | null;
  telegram?: string | null;
  social_links?: Record<string, string | null>;
  timezone?: string;
}

export interface ProfileUpdatePayload {
  display_name?: string | null;
  whatsapp?: string | null;
  telegram?: string | null;
  social_links?: Record<string, string | null>;
  timezone?: string;
}

export async function registerUser(payload: RegisterPayload): Promise<AuthSessionResponse> {
  const response = await apiRequest<AuthSessionResponse>("/api/auth/register", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  storeAuthToken(response.access_token);
  return response;
}

export async function loginUser(email: string, password: string): Promise<LoginResponse> {
  const response = await apiRequest<LoginResponse>("/api/auth/login", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ email, password }),
  });
  if (response.access_token) {
    storeAuthToken(response.access_token);
  }
  return response;
}

export async function completeMfaLogin(challengeToken: string, code: string): Promise<AuthSessionResponse> {
  const response = await apiRequest<AuthSessionResponse>("/api/auth/login/mfa", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ challenge_token: challengeToken, code }),
  });
  storeAuthToken(response.access_token);
  return response;
}

export async function logoutUser(): Promise<void> {
  await apiRequest<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
  storeAuthToken(null);
}

export async function loadAuthUser(): Promise<AuthUser | null> {
  return apiOptional<AuthUser>("/api/auth/me");
}

export async function updateProfile(payload: ProfileUpdatePayload): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/auth/me", {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
}

export async function updatePassword(currentPassword: string, newPassword: string): Promise<void> {
  await apiRequest<{ ok: boolean }>("/api/auth/password", {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  storeAuthToken(null);
  storeStepUpToken(null);
}

export async function createOrganization(name: string): Promise<AuthOrganization> {
  return apiRequest<AuthOrganization>("/api/auth/organizations", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ name }),
  });
}

export async function updateOrganization(organizationId: number, name: string): Promise<AuthOrganization> {
  return apiRequest<AuthOrganization>(`/api/auth/organizations/${organizationId}`, {
    method: "PATCH",
    headers: jsonHeaders,
    body: JSON.stringify({ name }),
  });
}

export async function deleteOrganization(organizationId: number): Promise<void> {
  await apiRequest<{ ok: boolean }>(`/api/auth/organizations/${organizationId}`, { method: "DELETE" });
}

export async function addOrganizationMember(organizationId: number, email: string, role: string): Promise<AuthOrganization> {
  return apiRequest<AuthOrganization>(`/api/auth/organizations/${organizationId}/members`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ email, role }),
  });
}

export async function loadOrganizationDetail(organizationId: number): Promise<AuthOrganizationDetail> {
  return apiRequest<AuthOrganizationDetail>(`/api/auth/organizations/${organizationId}`);
}

export async function createOrganizationInvite(organizationId: number, role: AuthOrganizationRole): Promise<AuthOrganizationInvite> {
  return apiRequest<AuthOrganizationInvite>(`/api/auth/organizations/${organizationId}/invites`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ role }),
  });
}

export async function revokeOrganizationInvite(organizationId: number, inviteId: number): Promise<void> {
  await apiRequest<{ ok: boolean }>(`/api/auth/organizations/${organizationId}/invites/${inviteId}`, { method: "DELETE" });
}

export async function acceptOrganizationInvite(token: string): Promise<AuthOrganization> {
  return apiRequest<AuthOrganization>(`/api/auth/organization-invites/${encodeURIComponent(token)}/accept`, { method: "POST" });
}

export async function removeOrganizationMember(organizationId: number, userId: number): Promise<void> {
  await apiRequest<{ ok: boolean }>(`/api/auth/organizations/${organizationId}/members/${userId}`, { method: "DELETE" });
}

export async function linkOrganizationPrinter(organizationId: number, printerId: number): Promise<void> {
  await apiRequest<{ ok: boolean }>(`/api/auth/organizations/${organizationId}/printers`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ printer_id: printerId }),
  });
}

export async function unlinkOrganizationPrinter(organizationId: number, printerId: number): Promise<void> {
  await apiRequest<{ ok: boolean }>(`/api/auth/organizations/${organizationId}/printers/${printerId}`, { method: "DELETE" });
}

export async function setupMfa(payload: { password?: string; code?: string }): Promise<MfaSetupResponse> {
  return apiRequest<MfaSetupResponse>("/api/auth/mfa/setup", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
}

export async function enableMfa(code: string): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/auth/mfa/enable", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ code }),
  });
}

export async function disableMfa(code: string): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/auth/mfa/disable", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ code }),
  });
}

export async function createStepUpToken(payload: { purpose: StepUpPurpose; password?: string; code?: string }): Promise<StepUpResponse> {
  const response = await apiRequest<StepUpResponse>("/api/auth/step-up", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  storeStepUpToken(response.step_up_token);
  return response;
}

export async function listSessions(): Promise<AuthSessionRecord[]> {
  return apiRequest<AuthSessionRecord[]>("/api/auth/sessions");
}

export async function revokeSession(sessionId: number): Promise<void> {
  await apiRequest<{ ok: boolean }>(`/api/auth/sessions/${sessionId}`, { method: "DELETE" });
}

export async function revokeOtherSessions(stepUpToken: string, requestKey: string): Promise<{ revoked: number }> {
  return apiRequest<{ revoked: number }>("/api/auth/sessions/revoke-others", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ step_up_token: stepUpToken, request_key: requestKey }),
  });
}

export async function exportAccount(stepUpToken: string, requestKey: string): Promise<AccountExportResponse> {
  return apiRequest<AccountExportResponse>("/api/auth/account/export", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ step_up_token: stepUpToken, request_key: requestKey }),
  });
}

export async function deactivateAccount(stepUpToken: string, requestKey: string): Promise<AccountRequestRecord> {
  return apiRequest<AccountRequestRecord>("/api/auth/account/deletion", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ step_up_token: stepUpToken, request_key: requestKey }),
  });
}

export async function createAgentCredential(label: string, organizationId?: number | null): Promise<AgentCredentialResponse> {
  return apiRequest<AgentCredentialResponse>("/api/auth/agent-credentials", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify({ label, organization_id: organizationId ?? null }),
  });
}

export async function listAgentCredentials(): Promise<AgentCredentialRecord[]> {
  return apiRequest<AgentCredentialRecord[]>("/api/auth/agent-credentials");
}
