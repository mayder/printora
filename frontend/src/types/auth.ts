export type AuthOrganizationRole = "owner" | "admin" | "operator";

export interface AuthOrganization {
  id: number;
  name: string;
  role: AuthOrganizationRole;
  owner_user_id: number;
}

export interface AuthUser {
  id: number;
  email: string;
  display_name?: string | null;
  whatsapp?: string | null;
  telegram?: string | null;
  social_links: Record<string, string | null>;
  mfa_enabled: boolean;
  is_active: boolean;
  created_at: string;
  organizations: AuthOrganization[];
}

export interface AuthSessionResponse {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: AuthUser;
}

export interface LoginResponse {
  access_token?: string | null;
  token_type: "bearer";
  expires_at?: string | null;
  user?: AuthUser | null;
  mfa_required: boolean;
  challenge_token?: string | null;
}

export interface MfaSetupResponse {
  secret: string;
  otpauth_uri: string;
}

export interface StepUpResponse {
  step_up_token: string;
  expires_at: string;
}

export interface AgentCredentialResponse {
  id: number;
  label: string;
  credential: string;
  credential_prefix: string;
  organization_id?: number | null;
  created_at: string;
}

export interface AgentCredentialRecord {
  id: number;
  label: string;
  credential_prefix: string;
  organization_id?: number | null;
  revoked: boolean;
  created_at: string;
  last_used_at?: string | null;
}
